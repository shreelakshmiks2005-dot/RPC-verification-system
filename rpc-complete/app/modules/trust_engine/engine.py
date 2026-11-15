"""
Trust Score Engine
Combines all module outputs into a final verification report
"""
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime


@dataclass
class ModuleScore:
    module: str
    score: int
    weight: float
    weighted_score: float
    status: str
    flags_count: int
    positive_flags: int
    negative_flags: int


@dataclass
class RiskIndicator:
    level: Literal["low", "medium", "high", "critical"]
    code: str
    message: str
    module: str


@dataclass
class TrustReport:
    # Overall
    trust_score: int  # 0-100
    authenticity_level: Literal["high", "medium", "low", "very_low"]
    risk_level: Literal["low", "medium", "high", "critical"]
    recommendation: str

    # Module breakdown
    module_scores: list[ModuleScore] = field(default_factory=list)

    # Risk analysis
    risk_indicators: list[RiskIndicator] = field(default_factory=list)

    # Metadata
    verification_id: str = ""
    candidate_id: str = ""
    timestamp: str = ""

    # Raw results
    resume_result: Optional[dict] = None
    project_result: Optional[dict] = None
    certificate_result: Optional[dict] = None


class TrustScoreEngine:
    """
    Combines verification results from all modules into a final trust score.

    Weighted scoring formula:
    - Resume: 30%
    - Project: 50%
    - Certificate: 20%
    """

    # Default weights (can be customized)
    DEFAULT_WEIGHTS = {
        "resume": 0.30,
        "project": 0.50,
        "certificate": 0.20,
    }

    # Risk thresholds
    RISK_THRESHOLDS = {
        "critical": 25,
        "high": 45,
        "medium": 65,
    }

    def __init__(self, weights: dict = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def calculate(
        self,
        resume_score: int = None,
        resume_status: str = None,
        resume_flags: list = None,
        project_score: int = None,
        project_status: str = None,
        project_flags: list = None,
        certificate_score: int = None,
        certificate_status: str = None,
        certificate_flags: list = None,
        candidate_id: str = "",
        verification_id: str = "",
    ) -> TrustReport:
        """
        Calculate the final trust score from all module results.

        Args:
            resume_score: Score from resume verification (0-100)
            resume_status: Status from resume verification
            resume_flags: Flags from resume verification
            project_score: Score from project verification (0-100)
            project_status: Status from project verification
            project_flags: Flags from project verification
            certificate_score: Score from certificate verification (0-100)
            certificate_status: Status from certificate verification
            certificate_flags: Flags from certificate verification

        Returns:
            TrustReport with overall trust score and breakdown
        """
        resume_flags = resume_flags or []
        project_flags = project_flags or []
        certificate_flags = certificate_flags or []

        module_scores = []
        risk_indicators = []
        total_weighted = 0.0
        total_weight = 0.0

        # Process Resume Module
        if resume_score is not None:
            weighted = resume_score * self.weights["resume"]
            pos, neg = self._count_flags(resume_flags)

            module_scores.append(ModuleScore(
                module="resume",
                score=resume_score,
                weight=self.weights["resume"],
                weighted_score=round(weighted, 2),
                status=resume_status or "unknown",
                flags_count=len(resume_flags),
                positive_flags=pos,
                negative_flags=neg,
            ))

            total_weighted += weighted
            total_weight += self.weights["resume"]

            # Check for risks
            self._check_module_risks(
                "resume", resume_score, resume_flags, risk_indicators
            )

        # Process Project Module
        if project_score is not None:
            weighted = project_score * self.weights["project"]
            pos, neg = self._count_flags(project_flags)

            module_scores.append(ModuleScore(
                module="project",
                score=project_score,
                weight=self.weights["project"],
                weighted_score=round(weighted, 2),
                status=project_status or "unknown",
                flags_count=len(project_flags),
                positive_flags=pos,
                negative_flags=neg,
            ))

            total_weighted += weighted
            total_weight += self.weights["project"]

            self._check_module_risks(
                "project", project_score, project_flags, risk_indicators
            )

        # Process Certificate Module
        if certificate_score is not None:
            weighted = certificate_score * self.weights["certificate"]
            pos, neg = self._count_flags(certificate_flags)

            module_scores.append(ModuleScore(
                module="certificate",
                score=certificate_score,
                weight=self.weights["certificate"],
                weighted_score=round(weighted, 2),
                status=certificate_status or "unknown",
                flags_count=len(certificate_flags),
                positive_flags=pos,
                negative_flags=neg,
            ))

            total_weighted += weighted
            total_weight += self.weights["certificate"]

            self._check_module_risks(
                "certificate", certificate_score, certificate_flags, risk_indicators
            )

        # Calculate final trust score
        if total_weight > 0:
            # Normalize if not all modules present
            trust_score = int(total_weighted / total_weight)
        else:
            trust_score = 0

        # Determine authenticity level
        authenticity_level = self._get_authenticity_level(trust_score)

        # Determine overall risk level
        risk_level = self._get_risk_level(trust_score, risk_indicators)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            trust_score, authenticity_level, risk_level, module_scores
        )

        return TrustReport(
            trust_score=trust_score,
            authenticity_level=authenticity_level,
            risk_level=risk_level,
            recommendation=recommendation,
            module_scores=module_scores,
            risk_indicators=risk_indicators,
            verification_id=verification_id,
            candidate_id=candidate_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    def _count_flags(self, flags: list) -> tuple[int, int]:
        """Count positive and negative flags."""
        positive = 0
        negative = 0
        for flag in flags:
            flag_type = flag.get("type") if isinstance(flag, dict) else getattr(flag, "type", None)
            if flag_type == "positive":
                positive += 1
            elif flag_type == "negative":
                negative += 1
        return positive, negative

    def _check_module_risks(
        self,
        module: str,
        score: int,
        flags: list,
        risk_indicators: list,
    ):
        """Check for risk indicators in a module."""
        # Low score risk
        if score < 25:
            risk_indicators.append(RiskIndicator(
                level="critical",
                code=f"{module.upper()}_VERY_LOW_SCORE",
                message=f"{module.title()} verification score critically low ({score})",
                module=module,
            ))
        elif score < 45:
            risk_indicators.append(RiskIndicator(
                level="high",
                code=f"{module.upper()}_LOW_SCORE",
                message=f"{module.title()} verification score is low ({score})",
                module=module,
            ))

        # Check specific high-risk flags
        high_risk_flags = {
            "IS_FORK": "Project is a fork of another repository",
            "FORK_OF_POPULAR": "Project is a fork of a popular tutorial",
            "BULK_INITIAL_COMMIT": "Project shows bulk code upload pattern",
            "NAME_MISMATCH": "Certificate name doesn't match candidate",
            "NO_TEXT": "Certificate appears to be invalid image",
            "COATTAIL": "Minimal contribution to claimed project",
        }

        for flag in flags:
            code = flag.get("code") if isinstance(flag, dict) else getattr(flag, "code", None)
            if code in high_risk_flags:
                risk_indicators.append(RiskIndicator(
                    level="high",
                    code=code,
                    message=high_risk_flags[code],
                    module=module,
                ))

    def _get_authenticity_level(self, score: int) -> str:
        """Determine authenticity level from score."""
        if score >= 75:
            return "high"
        elif score >= 50:
            return "medium"
        elif score >= 25:
            return "low"
        else:
            return "very_low"

    def _get_risk_level(self, score: int, risk_indicators: list) -> str:
        """Determine overall risk level."""
        # Check for critical indicators
        if any(r.level == "critical" for r in risk_indicators):
            return "critical"

        # Check score thresholds
        if score < self.RISK_THRESHOLDS["critical"]:
            return "critical"
        elif score < self.RISK_THRESHOLDS["high"]:
            return "high"
        elif score < self.RISK_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(
        self,
        score: int,
        authenticity: str,
        risk: str,
        modules: list,
    ) -> str:
        """Generate a recommendation based on the analysis."""
        if risk == "critical":
            return "REJECT: Multiple critical issues detected. High likelihood of fraudulent credentials."

        if risk == "high":
            return "MANUAL REVIEW REQUIRED: Significant concerns detected. Requires thorough manual verification."

        if authenticity == "high" and risk == "low":
            return "APPROVE: All verification checks passed. Credentials appear authentic."

        if authenticity == "medium":
            return "CONDITIONAL APPROVAL: Some minor concerns. Consider additional verification for specific modules."

        # Check specific module issues
        low_modules = [m.module for m in modules if m.score < 50]
        if low_modules:
            return f"REVIEW NEEDED: Low scores in {', '.join(low_modules)} module(s). Investigate before proceeding."

        return "PROCEED WITH CAUTION: Mixed results. Use judgment based on role requirements."
