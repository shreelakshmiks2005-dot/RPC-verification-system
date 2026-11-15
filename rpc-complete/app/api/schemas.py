"""
API Request/Response Schemas for RPC Verification System
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ============== Common ==============

class FlagSchema(BaseModel):
    type: Literal["positive", "warning", "negative"]
    code: str
    message: str


class RiskIndicatorSchema(BaseModel):
    level: Literal["low", "medium", "high", "critical"]
    code: str
    message: str
    module: str


class ModuleScoreSchema(BaseModel):
    module: str
    score: int
    weight: float
    weighted_score: float
    status: str
    flags_count: int
    positive_flags: int
    negative_flags: int


# ============== Resume Module ==============

class ResumeVerifyRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)
    required_skills: list[str] = []
    preferred_skills: list[str] = []


class ExtractedResumeSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = []
    github_links: list[str] = []
    linkedin: Optional[str] = None


class SkillMatchSchema(BaseModel):
    total_skills_found: int
    required_skills_matched: int
    required_skills_total: int
    match_percentage: float
    missing_required: list[str] = []
    additional_skills: list[str] = []


class ResumeVerifyResponse(BaseModel):
    candidate_id: str
    verification_id: str
    score: int
    status: Literal["verified", "needs_review", "suspicious"]
    extracted_data: ExtractedResumeSchema
    skill_analysis: Optional[SkillMatchSchema] = None
    flags: list[FlagSchema] = []
    details: dict = {}


# ============== Project Module ==============

class ProjectVerifyRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)
    github_username: str = Field(..., min_length=1)
    repo_link: str
    project_type: Literal["individual", "group"]


class ProjectDetailsSchema(BaseModel):
    owner: Optional[str] = None
    is_fork: Optional[bool] = None
    candidate_commits: Optional[int] = None
    total_commits: Optional[int] = None
    candidate_lines_added: Optional[int] = None
    pr_count: Optional[int] = None
    contributors_count: Optional[int] = None


class ProjectVerifyResponse(BaseModel):
    candidate_id: str
    verification_id: str
    score: int
    status: Literal["verified", "needs_review", "suspicious"]
    tier1_complete: bool
    tier2_complete: bool
    tier2_status: str
    flags: list[FlagSchema] = []
    details: ProjectDetailsSchema = ProjectDetailsSchema()


# ============== Certificate Module ==============

class CertificateVerifyRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)
    expected_course: Optional[str] = None
    verify_online: bool = True


class ExtractedCertificateSchema(BaseModel):
    candidate_name: Optional[str] = None
    issuer: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_id: Optional[str] = None
    verification_url: Optional[str] = None
    has_qr: bool = False


class CertificateVerifyResponse(BaseModel):
    candidate_id: str
    verification_id: str
    score: int
    status: Literal["verified", "needs_review", "suspicious"]
    extracted_data: ExtractedCertificateSchema
    flags: list[FlagSchema] = []
    online_verified: Optional[bool] = None
    details: dict = {}


# ============== Full Verification ==============

class FullVerifyRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)

    # Project info
    github_username: Optional[str] = None
    repo_link: Optional[str] = None
    project_type: Literal["individual", "group"] = "individual"

    # Resume/Certificate are uploaded as files
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    verify_certificates_online: bool = True


class FullVerifyResponse(BaseModel):
    candidate_id: str
    verification_id: str

    # Overall trust score
    trust_score: int
    authenticity_level: Literal["high", "medium", "low", "very_low"]
    risk_level: Literal["low", "medium", "high", "critical"]
    recommendation: str

    # Module breakdown
    module_scores: list[ModuleScoreSchema] = []
    risk_indicators: list[RiskIndicatorSchema] = []

    # Individual results (dict format for flexibility)
    resume_result: Optional[dict] = None
    project_result: Optional[dict] = None
    certificate_result: Optional[dict] = None

    timestamp: datetime
