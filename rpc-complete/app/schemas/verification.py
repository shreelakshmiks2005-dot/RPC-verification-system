from pydantic import BaseModel, field_validator, Field
from typing import Optional, Literal
from datetime import datetime
import re


class VerificationRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)
    github_username: str = Field(..., min_length=1)
    repo_link: str
    project_type: Literal["individual", "group"]

    @field_validator("repo_link")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        # Strip trailing .git and slash before validating
        v = v.strip().rstrip("/")
        if v.endswith(".git"):
            v = v[:-4]
        pattern = r"^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+"
        if not re.match(pattern, v):
            raise ValueError("Must be a valid GitHub repository URL (https://github.com/owner/repo)")
        return v


class FlagSchema(BaseModel):
    type: Literal["positive", "warning", "negative"]
    code: str
    message: str


class VerificationDetails(BaseModel):
    owner: Optional[str] = None
    is_fork: Optional[bool] = None
    candidate_commits: Optional[int] = None
    total_commits: Optional[int] = None
    candidate_lines_added: Optional[int] = None
    file_types_touched: Optional[list[str]] = None
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None
    pr_count: Optional[int] = None
    issue_count: Optional[int] = None
    contributors_count: Optional[int] = None


class VerificationResponse(BaseModel):
    candidate_id: str
    verification_type: str = "project"
    verification_id: str
    score: int
    max_score: int = 100
    status: Literal["verified", "needs_review", "suspicious"]
    tier1_complete: bool
    tier2_complete: bool
    tier2_status: Literal["pending", "complete", "completed", "not_required", "failed", "error"]
    flags: list[FlagSchema] = []
    details: VerificationDetails = VerificationDetails()
    created_at: datetime


class ErrorResponse(BaseModel):
    error: bool = True
    code: Literal[
        "REPO_NOT_FOUND",
        "INVALID_USERNAME",
        "INVALID_URL",
        "RATE_LIMITED",
        "INTERNAL_ERROR",
    ]
    message: str
