from fastapi import FastAPI, HTTPException
from datetime import datetime
import uuid

from app.config import get_settings
from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
    FlagSchema,
    VerificationDetails,
    ErrorResponse,
)
from app.services.github_client import GitHubClient, RepoNotFoundError, RateLimitError
from app.services.tier1_verifier import Tier1Verifier
from app.services.tier2_verifier import Tier2Verifier
from app.services.fingerprint_matcher import FingerprintMatcher

app = FastAPI(
    title="Project Verification API",
    description="Verify GitHub project contributions",
    version="1.0.0",
)

# In-memory storage for now (Task 9 adds proper DB)
verifications_store: dict[str, dict] = {}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
    }


@app.post("/verify-project", response_model=VerificationResponse)
async def verify_project(request: VerificationRequest):
    settings = get_settings()
    github_client = GitHubClient(token=settings.github_token)
    verifier = Tier1Verifier(github_client)

    try:
        result = await verifier.verify(
            github_username=request.github_username,
            repo_url=request.repo_link,
            project_type=request.project_type,
        )
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

    verification_id = f"ver_{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow()

    # Determine if Tier 2 is needed
    needs_tier2 = result.score < 75
    tier2_result = None
    tier2_flags = []

    if needs_tier2:
        # Run Tier 2 inline (plagiarism + AI analysis)
        try:
            fingerprint_matcher = FingerprintMatcher()
            tier2_verifier = Tier2Verifier(
                github_client=github_client,
                fingerprint_matcher=fingerprint_matcher,
                openai_api_key=settings.openai_api_key,
                anthropic_api_key=settings.anthropic_api_key,
            )
            tier2_result = await tier2_verifier.analyze(
                repo_url=request.repo_link,
                github_username=request.github_username,
            )
            tier2_flags = tier2_result.flags if tier2_result else []
            tier2_status = "complete"
        except Exception as e:
            tier2_status = "error"
    else:
        tier2_status = "not_required"

    # Build response - combine Tier 1 and Tier 2 flags
    all_flags = list(result.flags) + tier2_flags
    flags = [
        FlagSchema(type=f.type, code=f.code, message=f.message)
        for f in all_flags
    ]

    # Recalculate score if Tier 2 found issues
    final_score = result.score
    if tier2_result and tier2_result.score_adjustment:
        final_score = max(0, min(100, result.score + tier2_result.score_adjustment))

    details = VerificationDetails(
        owner=result.details.get("owner"),
        is_fork=result.details.get("is_fork"),
        candidate_commits=result.details.get("candidate_commits"),
        total_commits=result.details.get("total_commits"),
        candidate_lines_added=result.details.get("candidate_lines_added"),
        file_types_touched=result.details.get("file_types_touched"),
        pr_count=result.details.get("pr_count"),
        contributors_count=result.details.get("contributors_count"),
    )

    # Determine final status based on final score
    from app.services.scoring import determine_status
    final_status = determine_status(final_score)

    response = VerificationResponse(
        candidate_id=request.candidate_id,
        verification_id=verification_id,
        score=final_score,
        status=final_status,
        tier1_complete=True,
        tier2_complete=(tier2_status in ["complete", "not_required"]),
        tier2_status=tier2_status,
        flags=flags,
        details=details,
        created_at=created_at,
    )

    # Store for later retrieval
    verifications_store[verification_id] = response.model_dump()

    # TODO: Queue Tier 2 job if needed (Task 7)

    return response


@app.get("/verify-project/{verification_id}", response_model=VerificationResponse)
async def get_verification(verification_id: str):
    if verification_id not in verifications_store:
        raise HTTPException(
            status_code=404,
            detail={"error": True, "code": "NOT_FOUND", "message": "Verification not found"},
        )

    data = verifications_store[verification_id]
    return VerificationResponse(**data)
