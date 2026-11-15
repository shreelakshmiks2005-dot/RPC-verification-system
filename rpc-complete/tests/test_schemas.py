import pytest
from pydantic import ValidationError


def test_verification_request_validates_github_url():
    from app.schemas.verification import VerificationRequest

    with pytest.raises(ValidationError):
        VerificationRequest(
            candidate_id="123",
            candidate_name="Test",
            github_username="user",
            repo_link="not-a-github-url",
            project_type="individual",
        )


def test_verification_request_rejects_gitlab_url():
    from app.schemas.verification import VerificationRequest

    with pytest.raises(ValidationError):
        VerificationRequest(
            candidate_id="123",
            candidate_name="Test",
            github_username="user",
            repo_link="https://gitlab.com/user/repo",
            project_type="individual",
        )


def test_verification_request_accepts_valid_url():
    from app.schemas.verification import VerificationRequest

    req = VerificationRequest(
        candidate_id="123",
        candidate_name="Test",
        github_username="user",
        repo_link="https://github.com/owner/repo",
        project_type="individual",
    )
    assert req.repo_link == "https://github.com/owner/repo"


def test_verification_request_accepts_valid_url_with_trailing_slash():
    from app.schemas.verification import VerificationRequest

    req = VerificationRequest(
        candidate_id="123",
        candidate_name="Test",
        github_username="user",
        repo_link="https://github.com/owner/repo/",
        project_type="group",
    )
    assert "github.com" in req.repo_link
