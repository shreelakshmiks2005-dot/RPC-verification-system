import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.database import Base


class ProjectType(str, enum.Enum):
    individual = "individual"
    group = "group"


class VerificationStatus(str, enum.Enum):
    verified = "verified"
    needs_review = "needs_review"
    suspicious = "suspicious"


class Tier2Status(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    not_required = "not_required"
    failed = "failed"


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_username: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_link: Mapped[str] = mapped_column(Text, nullable=False)
    project_type: Mapped[str] = mapped_column(
        SQLEnum(ProjectType), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.suspicious
    )
    tier1_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    tier2_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    tier2_status: Mapped[str] = mapped_column(
        SQLEnum(Tier2Status), default=Tier2Status.not_required
    )
    flags: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
