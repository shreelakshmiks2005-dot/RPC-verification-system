import uuid


def test_verification_model_has_required_fields():
    from app.models.verification import Verification

    v = Verification(
        id=uuid.uuid4(),
        candidate_id="123",
        candidate_name="Test",
        github_username="testuser",
        repo_link="https://github.com/test/repo",
        project_type="individual",
        score=75,
        status="verified",
    )
    assert v.candidate_id == "123"
    assert v.status == "verified"
    assert v.project_type == "individual"
