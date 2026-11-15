from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import pytest


def test_health_returns_ok():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_verify_project_returns_verification_response():
    from app.main import app
    from app.services.tier1_verifier import Tier1Result, Flag

    mock_result = Tier1Result(
        score=82,
        status="verified",
        flags=[Flag("positive", "IS_OWNER", "Owner")],
        details={"owner": "testuser", "candidate_commits": 10},
        checks=[],
    )

    with patch("app.main.Tier1Verifier") as MockVerifier:
        mock_instance = MagicMock()
        mock_instance.verify = AsyncMock(return_value=mock_result)
        MockVerifier.return_value = mock_instance

        with patch("app.main.GitHubClient"):
            client = TestClient(app)
            response = client.post(
                "/verify-project",
                json={
                    "candidate_id": "123",
                    "candidate_name": "Test User",
                    "github_username": "testuser",
                    "repo_link": "https://github.com/testuser/myrepo",
                    "project_type": "individual",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["score"] == 82
            assert data["status"] == "verified"
            assert data["verification_id"].startswith("ver_")
            assert data["tier1_complete"] is True


def test_verify_project_rejects_invalid_github_url():
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/verify-project",
        json={
            "candidate_id": "123",
            "candidate_name": "Test",
            "github_username": "user",
            "repo_link": "https://gitlab.com/user/repo",
            "project_type": "individual",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


def test_get_verification_not_found():
    from app.main import app

    client = TestClient(app)
    response = client.get("/verify-project/ver_nonexistent")
    assert response.status_code == 404
