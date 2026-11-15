import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_parse_repo_url_extracts_owner_and_repo():
    from app.services.github_client import GitHubClient

    client = GitHubClient(token="fake")
    owner, repo = client.parse_repo_url("https://github.com/rahuldev/ai-project")
    assert owner == "rahuldev"
    assert repo == "ai-project"


def test_parse_repo_url_handles_trailing_slash():
    from app.services.github_client import GitHubClient

    client = GitHubClient(token="fake")
    owner, repo = client.parse_repo_url("https://github.com/rahuldev/ai-project/")
    assert owner == "rahuldev"
    assert repo == "ai-project"


def test_parse_repo_url_raises_on_invalid():
    from app.services.github_client import GitHubClient

    client = GitHubClient(token="fake")
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        client.parse_repo_url("https://gitlab.com/user/repo")


def test_parse_repo_url_raises_on_missing_repo():
    from app.services.github_client import GitHubClient

    client = GitHubClient(token="fake")
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        client.parse_repo_url("https://github.com/useronly")


@pytest.mark.asyncio
async def test_get_repo_returns_repo_data():
    from app.services.github_client import GitHubClient

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "fork": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-06-01T00:00:00Z",
        "stargazers_count": 10,
        "owner": {"login": "rahuldev"},
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        MockClient.return_value = mock_client_instance

        client = GitHubClient(token="fake")
        data = await client.get_repo("rahuldev", "ai-project")

        assert data.is_fork is False
        assert data.owner == "rahuldev"
        assert data.stars == 10


@pytest.mark.asyncio
async def test_get_repo_raises_on_404():
    from app.services.github_client import GitHubClient, RepoNotFoundError

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Not Found"}

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        MockClient.return_value = mock_client_instance

        client = GitHubClient(token="fake")
        with pytest.raises(RepoNotFoundError):
            await client.get_repo("nonexistent", "repo")
