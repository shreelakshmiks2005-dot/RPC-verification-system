from typing import Literal


def calculate_score(checks: list[dict]) -> int:
    total = sum(check["points"] for check in checks if check.get("passed", False))
    return max(0, min(100, total))


def determine_status(score: int) -> Literal["verified", "needs_review", "suspicious"]:
    if score >= 75:
        return "verified"
    elif score >= 45:
        return "needs_review"
    else:
        return "suspicious"
