"""
API Routes for RPC Verification System
"""
import uuid
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.schemas import (
    ResumeVerifyRequest, ResumeVerifyResponse, ExtractedResumeSchema, SkillMatchSchema,
    ProjectVerifyRequest, ProjectVerifyResponse, ProjectDetailsSchema,
    CertificateVerifyRequest, CertificateVerifyResponse, ExtractedCertificateSchema,
    FullVerifyRequest, FullVerifyResponse,
    FlagSchema, ModuleScoreSchema, RiskIndicatorSchema,
)

# Import modules
from app.modules.resume import ResumeVerifier
from app.modules.certificate import CertificateVerifier
from app.modules.project import GitHubClient, Tier1Verifier, Tier2Verifier, RepoNotFoundError, RateLimitError
from app.modules.trust_engine import TrustScoreEngine


router = APIRouter()


# ============== Resume Endpoints ==============

@router.post("/verify-resume", response_model=ResumeVerifyResponse)
async def verify_resume(
    candidate_id: str = Form(...),
    candidate_name: str = Form(...),
    required_skills: str = Form(""),  # Comma-separated
    preferred_skills: str = Form(""),  # Comma-separated
    file: UploadFile = File(...),
):
    """
    Verify a resume file (PDF, DOCX, TXT).
    Extracts skills, contact info, and GitHub links.
    """
    # Parse skills
    req_skills = [s.strip() for s in required_skills.split(",") if s.strip()]
    pref_skills = [s.strip() for s in preferred_skills.split(",") if s.strip()]

    # Read file
    content = await file.read()

    # Verify
    verifier = ResumeVerifier()
    try:
        result = await verifier.verify(
            file_content=content,
            filename=file.filename,
            required_skills=req_skills,
            preferred_skills=pref_skills,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {e}")

    verification_id = f"res_{uuid.uuid4().hex[:12]}"

    # Build response
    extracted = ExtractedResumeSchema(
        name=result.extracted_data.name,
        email=result.extracted_data.email,
        phone=result.extracted_data.phone,
        skills=result.extracted_data.skills,
        github_links=result.extracted_data.github_links,
        linkedin=result.extracted_data.linkedin,
    )

    skill_analysis = None
    if result.skill_analysis:
        skill_analysis = SkillMatchSchema(
            total_skills_found=result.skill_analysis.total_skills_found,
            required_skills_matched=result.skill_analysis.required_skills_matched,
            required_skills_total=result.skill_analysis.required_skills_total,
            match_percentage=result.skill_analysis.match_percentage,
            missing_required=result.skill_analysis.missing_required,
            additional_skills=result.skill_analysis.additional_skills,
        )

    flags = [
        FlagSchema(type=f.type, code=f.code, message=f.message)
        for f in result.flags
    ]

    return ResumeVerifyResponse(
        candidate_id=candidate_id,
        verification_id=verification_id,
        score=result.score,
        status=result.status,
        extracted_data=extracted,
        skill_analysis=skill_analysis,
        flags=flags,
        details=result.details,
    )


# ============== Project Endpoints ==============

@router.post("/verify-project", response_model=ProjectVerifyResponse)
async def verify_project(request: ProjectVerifyRequest):
    """
    Verify a GitHub project contribution.
    Checks ownership, commits, plagiarism patterns.
    """
    settings = get_settings()
    github_client = GitHubClient(token=settings.github_token)
    tier1_verifier = Tier1Verifier(github_client)
    tier2_verifier = Tier2Verifier(github_client=github_client)

    try:
        # Tier 1 verification
        tier1_result = await tier1_verifier.verify(
            github_username=request.github_username,
            repo_url=request.repo_link,
            project_type=request.project_type,
        )

        # Tier 2 if needed
        tier2_flags = []
        tier2_status = "not_required"
        if tier1_result.score < 75:
            try:
                tier2_result = await tier2_verifier.analyze(
                    repo_url=request.repo_link,
                    github_username=request.github_username,
                )
                tier2_flags = tier2_result.flags
                tier2_status = "complete"

                # Adjust score
                final_score = max(0, min(100, tier1_result.score + tier2_result.score_adjustment))
            except Exception:
                tier2_status = "error"
                final_score = tier1_result.score
        else:
            final_score = tier1_result.score

    except RepoNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": True, "code": "REPO_NOT_FOUND", "message": "Repository not found or is private"},
        )
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail={"error": True, "code": "RATE_LIMITED", "message": "GitHub API rate limit exceeded"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": True, "code": "INVALID_URL", "message": str(e)},
        )

    verification_id = f"prj_{uuid.uuid4().hex[:12]}"

    # Combine flags
    all_flags = list(tier1_result.flags) + tier2_flags
    flags = [
        FlagSchema(type=f.type, code=f.code, message=f.message)
        for f in all_flags
    ]

    # Determine status
    from app.services.scoring import determine_status
    final_status = determine_status(final_score)

    details = ProjectDetailsSchema(
        owner=tier1_result.details.get("owner"),
        is_fork=tier1_result.details.get("is_fork"),
        candidate_commits=tier1_result.details.get("candidate_commits"),
        total_commits=tier1_result.details.get("total_commits"),
        candidate_lines_added=tier1_result.details.get("candidate_lines_added"),
        pr_count=tier1_result.details.get("pr_count"),
        contributors_count=tier1_result.details.get("contributors_count"),
    )

    return ProjectVerifyResponse(
        candidate_id=request.candidate_id,
        verification_id=verification_id,
        score=final_score,
        status=final_status,
        tier1_complete=True,
        tier2_complete=(tier2_status in ["complete", "not_required"]),
        tier2_status=tier2_status,
        flags=flags,
        details=details,
    )


# ============== Certificate Endpoints ==============

@router.post("/verify-certificate", response_model=CertificateVerifyResponse)
async def verify_certificate(
    candidate_id: str = Form(...),
    candidate_name: str = Form(...),
    expected_course: str = Form(""),
    verify_online: bool = Form(True),
    file: UploadFile = File(...),
):
    """
    Verify a certificate image/PDF.
    Extracts text via OCR, decodes QR codes, validates online.
    """
    content = await file.read()

    verifier = CertificateVerifier()
    try:
        result = await verifier.verify(
            file_content=content,
            filename=file.filename,
            expected_name=candidate_name,
            expected_course=expected_course or None,
            verify_online=verify_online,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {e}")

    verification_id = f"crt_{uuid.uuid4().hex[:12]}"

    extracted = ExtractedCertificateSchema(
        candidate_name=result.extracted_data.candidate_name,
        issuer=result.extracted_data.issuer,
        course_name=result.extracted_data.course_name,
        issue_date=result.extracted_data.issue_date,
        certificate_id=result.extracted_data.certificate_id,
        verification_url=result.extracted_data.verification_url,
        has_qr=bool(result.extracted_data.qr_data),
    )

    flags = [
        FlagSchema(type=f.type, code=f.code, message=f.message)
        for f in result.flags
    ]

    online_verified = None
    if result.online_verification:
        online_verified = result.online_verification.get("verified")

    return CertificateVerifyResponse(
        candidate_id=candidate_id,
        verification_id=verification_id,
        score=result.score,
        status=result.status,
        extracted_data=extracted,
        flags=flags,
        online_verified=online_verified,
        details=result.details,
    )


# ============== Full Verification Endpoint ==============

@router.post("/verify-full", response_model=FullVerifyResponse)
async def verify_full(
    candidate_id: str = Form(...),
    candidate_name: str = Form(...),
    github_username: str = Form(""),
    repo_link: str = Form(""),
    project_type: str = Form("individual"),
    required_skills: str = Form(""),
    preferred_skills: str = Form(""),
    verify_certificates_online: bool = Form(True),
    resume_file: Optional[UploadFile] = File(None),
    certificate_file: Optional[UploadFile] = File(None),
):
    """
    Full verification: Resume + Project + Certificate.
    Combines all modules into a final trust score.
    """
    verification_id = f"full_{uuid.uuid4().hex[:12]}"

    req_skills = [s.strip() for s in required_skills.split(",") if s.strip()]
    pref_skills = [s.strip() for s in preferred_skills.split(",") if s.strip()]

    resume_result = None
    project_result = None
    certificate_result = None
    cross_check_flags = []  # flags from cross-module validation

    # 1. Verify Resume (if provided)
    resume_github_links = []
    if resume_file:
        content = await resume_file.read()
        verifier = ResumeVerifier()
        try:
            result = await verifier.verify(
                file_content=content,
                filename=resume_file.filename,
                required_skills=req_skills,
                preferred_skills=pref_skills,
            )
            resume_result = {
                "score": result.score,
                "status": result.status,
                "flags": [{"type": f.type, "code": f.code, "message": f.message} for f in result.flags],
            }
            # Capture GitHub links found in resume for cross-check
            resume_github_links = result.extracted_data.github_links or []
        except Exception as e:
            resume_result = {"score": 0, "status": "error", "error": str(e), "flags": []}

    # Cross-check: GitHub username in resume vs submitted github_username
    # For GROUP projects: resume link belongs to the contributor, not necessarily the repo owner
    # → mismatch is a warning only, no score penalty
    # For INDIVIDUAL projects: resume link MUST match submitted username
    # → mismatch is a negative flag with score penalty
    if github_username and resume_github_links:
        username_lower = github_username.lower()
        # Use same fuzzy match as commit matching — strips dots/dashes
        def fuzzy_match(link: str, uname: str) -> bool:
            link_l = link.lower()
            if uname in link_l:
                return True
            clean_u = uname.replace("-","").replace("_","").replace(".","")
            clean_l = link_l.replace("-","").replace("_","").replace(".","")
            return clean_u[:10] in clean_l
        matched = any(fuzzy_match(link, username_lower) for link in resume_github_links)

        if matched:
            cross_check_flags.append({
                "type": "positive",
                "code": "GITHUB_RESUME_MATCH",
                "message": f"GitHub username '{github_username}' found in resume — identity confirmed"
            })
        else:
            if project_type == "group":
                # Group project: different contributor submitting same repo — expected
                cross_check_flags.append({
                    "type": "warning",
                    "code": "GITHUB_RESUME_DIFFERENT_MEMBER",
                    "message": (
                        f"Resume GitHub link ({', '.join(resume_github_links[:1])}) differs from "
                        f"submitted username '{github_username}' — normal for group projects "
                        f"where repo owner and contributor differ"
                    )
                })
                # No score penalty for group projects
            else:
                # Individual project: resume GitHub should match submitted username
                cross_check_flags.append({
                    "type": "negative",
                    "code": "GITHUB_RESUME_MISMATCH",
                    "message": (
                        f"Resume GitHub link(s) ({', '.join(resume_github_links[:2])}) "
                        f"don't match submitted username '{github_username}' — "
                        f"verify this is the correct GitHub account"
                    )
                })

    # 2. Verify Project (if provided)
    if github_username and repo_link:
        settings = get_settings()
        github_client = GitHubClient(token=settings.github_token)
        tier1_verifier = Tier1Verifier(github_client)
        tier2_verifier = Tier2Verifier(github_client=github_client)

        try:
            tier1_result = await tier1_verifier.verify(
                github_username=github_username,
                repo_url=repo_link,
                project_type=project_type,
            )

            tier2_flags = []
            if tier1_result.score < 75:
                try:
                    tier2_result = await tier2_verifier.analyze(
                        repo_url=repo_link,
                        github_username=github_username,
                    )
                    tier2_flags = tier2_result.flags
                    final_score = max(0, min(100, tier1_result.score + tier2_result.score_adjustment))
                except:
                    final_score = tier1_result.score
            else:
                final_score = tier1_result.score

            all_flags = list(tier1_result.flags) + tier2_flags
            project_result = {
                "score": final_score,
                "status": determine_status(final_score),
                "flags": [{"type": f.type, "code": f.code, "message": f.message} for f in all_flags],
            }

            # Append cross-module flags (GitHub username vs resume mismatch)
            if cross_check_flags:
                project_result["flags"] = cross_check_flags + project_result["flags"]
                # Penalise only for INDIVIDUAL project identity mismatch
                for cf in cross_check_flags:
                    if cf["code"] == "GITHUB_RESUME_MISMATCH" and project_type == "individual":
                        project_result["score"] = max(0, project_result["score"] - 15)
                        project_result["status"] = determine_status(project_result["score"])
        except Exception as e:
            project_result = {"score": 0, "status": "error", "error": str(e), "flags": []}

    # 3. Verify Certificate (if provided)
    if certificate_file:
        content = await certificate_file.read()
        verifier = CertificateVerifier()
        try:
            result = await verifier.verify(
                file_content=content,
                filename=certificate_file.filename,
                expected_name=candidate_name,
                verify_online=verify_certificates_online,
            )
            certificate_result = {
                "score": result.score,
                "status": result.status,
                "flags": [{"type": f.type, "code": f.code, "message": f.message} for f in result.flags],
            }
        except Exception as e:
            certificate_result = {"score": 0, "status": "error", "error": str(e), "flags": []}

    # 4. Calculate Trust Score
    engine = TrustScoreEngine()
    report = engine.calculate(
        resume_score=resume_result["score"] if resume_result else None,
        resume_status=resume_result.get("status") if resume_result else None,
        resume_flags=resume_result.get("flags", []) if resume_result else None,
        project_score=project_result["score"] if project_result else None,
        project_status=project_result.get("status") if project_result else None,
        project_flags=project_result.get("flags", []) if project_result else None,
        certificate_score=certificate_result["score"] if certificate_result else None,
        certificate_status=certificate_result.get("status") if certificate_result else None,
        certificate_flags=certificate_result.get("flags", []) if certificate_result else None,
        candidate_id=candidate_id,
        verification_id=verification_id,
    )

    # Build response
    module_scores = [
        ModuleScoreSchema(
            module=m.module,
            score=m.score,
            weight=m.weight,
            weighted_score=m.weighted_score,
            status=m.status,
            flags_count=m.flags_count,
            positive_flags=m.positive_flags,
            negative_flags=m.negative_flags,
        )
        for m in report.module_scores
    ]

    risk_indicators = [
        RiskIndicatorSchema(
            level=r.level,
            code=r.code,
            message=r.message,
            module=r.module,
        )
        for r in report.risk_indicators
    ]

    return FullVerifyResponse(
        candidate_id=candidate_id,
        verification_id=verification_id,
        trust_score=report.trust_score,
        authenticity_level=report.authenticity_level,
        risk_level=report.risk_level,
        recommendation=report.recommendation,
        module_scores=module_scores,
        risk_indicators=risk_indicators,
        resume_result=resume_result,
        project_result=project_result,
        certificate_result=certificate_result,
        timestamp=datetime.utcnow(),
    )


# Helper for project status
def determine_status(score: int) -> str:
    if score >= 75:
        return "verified"
    elif score >= 45:
        return "needs_review"
    return "suspicious"
