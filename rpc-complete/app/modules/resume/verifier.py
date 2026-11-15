"""
Resume Verification Module
Verifies resume authenticity and extracts structured data
"""
from dataclasses import dataclass, field
from typing import Optional

from .extractor import ResumeExtractor, ExtractedResume
from .skill_matcher import SkillMatcher, SkillMatchResult


@dataclass
class ResumeFlag:
    type: str  # "positive", "warning", "negative"
    code: str
    message: str


@dataclass
class ResumeVerificationResult:
    score: int  # 0-100
    status: str  # "verified", "needs_review", "suspicious"
    extracted_data: ExtractedResume
    skill_analysis: Optional[SkillMatchResult] = None
    flags: list[ResumeFlag] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class ResumeVerifier:
    """Verifies resume content and extracts structured data."""

    def __init__(self):
        self.extractor = ResumeExtractor()
        self.skill_matcher = SkillMatcher()

    async def verify(
        self,
        file_path: str = None,
        file_content: bytes = None,
        filename: str = None,
        required_skills: list[str] = None,
        preferred_skills: list[str] = None,
    ) -> ResumeVerificationResult:
        """
        Verify a resume file.

        Args:
            file_path: Path to resume file (PDF, DOCX, TXT)
            file_content: Raw file bytes (alternative to file_path)
            filename: Original filename (required if using file_content)
            required_skills: Must-have skills to check
            preferred_skills: Nice-to-have skills to check

        Returns:
            ResumeVerificationResult with score and extracted data
        """
        # Extract resume content
        if file_path:
            extracted = await self.extractor.extract_from_file(file_path)
        elif file_content and filename:
            extracted = await self.extractor.extract_from_bytes(file_content, filename)
        else:
            raise ValueError("Provide either file_path or (file_content + filename)")

        flags = []
        score = 50  # Base score

        # Check 1: Has contact info
        has_email = bool(extracted.email)
        has_phone = bool(extracted.phone)

        if has_email:
            flags.append(ResumeFlag("positive", "HAS_EMAIL", f"Email found: {extracted.email}"))
            score += 10
        else:
            flags.append(ResumeFlag("warning", "NO_EMAIL", "No email address found"))
            score -= 5

        if has_phone:
            flags.append(ResumeFlag("positive", "HAS_PHONE", "Phone number found"))
            score += 5

        # Check 2: Has skills
        if extracted.skills:
            skill_count = len(extracted.skills)
            flags.append(ResumeFlag(
                "positive", "HAS_SKILLS",
                f"Found {skill_count} technical skills"
            ))
            if skill_count >= 5:
                score += 15
            elif skill_count >= 3:
                score += 10
            else:
                score += 5
        else:
            flags.append(ResumeFlag("warning", "NO_SKILLS", "No technical skills detected"))
            score -= 10

        # Check 3: Has GitHub links
        if extracted.github_links:
            flags.append(ResumeFlag(
                "positive", "HAS_GITHUB",
                f"Found {len(extracted.github_links)} GitHub link(s)"
            ))
            score += 10
        else:
            flags.append(ResumeFlag("warning", "NO_GITHUB", "No GitHub profile found"))

        # Check 4: Has LinkedIn
        if extracted.linkedin:
            flags.append(ResumeFlag("positive", "HAS_LINKEDIN", "LinkedIn profile found"))
            score += 5

        # Check 5: Resume length check
        word_count = len(extracted.raw_text.split())
        if word_count < 50:
            flags.append(ResumeFlag(
                "negative", "TOO_SHORT",
                f"Resume is very short ({word_count} words)"
            ))
            score -= 20
        elif word_count < 150:
            flags.append(ResumeFlag(
                "warning", "SHORT_RESUME",
                f"Resume is quite short ({word_count} words)"
            ))
            score -= 5
        elif word_count > 2000:
            flags.append(ResumeFlag(
                "warning", "TOO_LONG",
                f"Resume is very long ({word_count} words)"
            ))

        # Check 6: Name detection
        if extracted.name:
            flags.append(ResumeFlag("positive", "HAS_NAME", f"Name detected: {extracted.name}"))
            score += 5
        else:
            flags.append(ResumeFlag("warning", "NO_NAME", "Could not detect candidate name"))

        # Skill matching if requirements provided
        skill_analysis = None
        if required_skills or preferred_skills:
            skill_analysis = self.skill_matcher.match(
                resume_skills=extracted.skills,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
            )

            if skill_analysis.match_percentage >= 80:
                flags.append(ResumeFlag(
                    "positive", "GOOD_SKILL_MATCH",
                    f"{skill_analysis.match_percentage}% of required skills matched"
                ))
                score += 10
            elif skill_analysis.match_percentage >= 50:
                flags.append(ResumeFlag(
                    "warning", "PARTIAL_SKILL_MATCH",
                    f"Only {skill_analysis.match_percentage}% of required skills matched"
                ))
            else:
                flags.append(ResumeFlag(
                    "negative", "LOW_SKILL_MATCH",
                    f"Only {skill_analysis.match_percentage}% of required skills matched"
                ))
                score -= 10

            if skill_analysis.missing_required:
                flags.append(ResumeFlag(
                    "warning", "MISSING_SKILLS",
                    f"Missing: {', '.join(skill_analysis.missing_required[:5])}"
                ))

        # Clamp score
        score = max(0, min(100, score))

        # Determine status
        if score >= 70:
            status = "verified"
        elif score >= 40:
            status = "needs_review"
        else:
            status = "suspicious"

        # Build details
        details = {
            "word_count": word_count,
            "skills_found": len(extracted.skills),
            "github_links": len(extracted.github_links),
            "has_contact_info": has_email or has_phone,
        }

        return ResumeVerificationResult(
            score=score,
            status=status,
            extracted_data=extracted,
            skill_analysis=skill_analysis,
            flags=flags,
            details=details,
        )
