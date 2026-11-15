"""
Integration tests for the Project Verification API.

These tests run against the actual API with mocked GitHub responses.
For full end-to-end tests with real GitHub, set GITHUB_TOKEN in environment.

Run with: pytest tests/test_integration.py -v -m integration
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_github_data():
    """Mock GitHub API responses for integration tests."""
    repo_data = MagicMock()
    repo_data.owner = "testuser"
    repo_data.name = "test-repo"
    repo_data.is_fork = False
    repo_data.created_at = "2024-01-01T00:00:00Z"
    repo_data.updated_at = "2024-06-01T00:00:00Z"
    repo_data.stars = 5
    repo_data.parent_url = None

    contributors = [
        MagicMock(login="testuser", contributions=20),
        MagicMock(login="contributor2", contributions=10),
    ]

    commits = [
        MagicMock(
            sha=f"abc{i}",
            author="testuser",
            date=f"2024-0{i+1}-15T00:00:00Z",
            message=f"Commit {i}",
            additions=50,
            deletions=10,
            files_changed=["main.py", "utils.py"],
        )
        for i in range(10)
    ]

    return {
        "repo": repo_data,
        "contributors": contributors,
        "commits": commits,
        "prs": [],
    }


@pytest.mark.integration
def test_full_verification_flow(client, mock_github_data):
    """Test complete verification flow from submission to retrieval."""
    with patch("app.main.GitHubClient") as MockGitHubClient:
        mock_instance = MagicMock()
        mock_instance.parse_repo_url.return_value = ("testuser", "test-repo")
        mock_instance.get_repo = AsyncMock(return_value=mock_github_data["repo"])
        mock_instance.get_contributors = AsyncMock(return_value=mock_github_data["contributors"])
        mock_instance.get_commits = AsyncMock(return_value=mock_github_data["commits"])
        mock_instance.get_pull_requests = AsyncMock(return_value=mock_github_data["prs"])
        MockGitHubClient.return_value = mock_instance

        # Submit verification
        response = client.post(
            "/verify-project",
            json={
                "candidate_id": "integration-test-123",
                "candidate_name": "Test User",
                "github_username": "testuser",
                "repo_link": "https://github.com/testuser/test-repo",
                "project_type": "individual",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "verification_id" in data
        assert data["verification_id"].startswith("ver_")
        assert data["tier1_complete"] is True
        assert data["candidate_id"] == "integration-test-123"
        assert data["status"] in ["verified", "needs_review", "suspicious"]

        # Verify the score makes sense (owner + contributor + commits should be high)
        assert data["score"] >= 50

        # Retrieve verification
        ver_id = data["verification_id"]
        response = client.get(f"/verify-project/{ver_id}")
        assert response.status_code == 200
        assert response.json()["verification_id"] == ver_id


@pytest.mark.integration
def test_verification_for_non_contributor(client, mock_github_data):
    """Test that non-contributors get low scores."""
    with patch("app.main.GitHubClient") as MockGitHubClient:
        mock_instance = MagicMock()
        mock_instance.parse_repo_url.return_value = ("owner", "repo")
        mock_instance.get_repo = AsyncMock(return_value=mock_github_data["repo"])
        mock_instance.get_contributors = AsyncMock(return_value=mock_github_data["contributors"])
        mock_instance.get_commits = AsyncMock(return_value=[])  # No commits by this user
        mock_instance.get_pull_requests = AsyncMock(return_value=[])
        MockGitHubClient.return_value = mock_instance

        response = client.post(
            "/verify-project",
            json={
                "candidate_id": "fake-user-123",
                "candidate_name": "Fake User",
                "github_username": "fakeuser",
                "repo_link": "https://github.com/owner/repo",
                "project_type": "individual",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Non-contributor should get low score
        assert data["score"] < 45
        assert data["status"] == "suspicious"


@pytest.mark.integration
def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.integration
def test_invalid_github_url_rejected(client):
    """Test that non-GitHub URLs are rejected."""
    response = client.post(
        "/verify-project",
        json={
            "candidate_id": "test",
            "candidate_name": "Test",
            "github_username": "user",
            "repo_link": "https://gitlab.com/user/repo",
            "project_type": "individual",
        },
    )

    assert response.status_code == 422  # Validation error
