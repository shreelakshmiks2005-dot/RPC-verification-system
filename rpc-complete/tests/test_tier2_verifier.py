import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_tier2_detects_fork():
    from app.services.tier2_verifier import Tier2Verifier

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "fork": True,
        "parent": {
            "full_name": "original/repo",
            "stargazers_count": 5000
        }
    }

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClient.return_value = mock_instance

        verifier = Tier2Verifier(github_token="fake")
        result = await verifier.analyze(owner="user", repo="copied-repo", github_username="user")

        # Should detect popular repo fork (IS_FORK is added by Tier 1, not Tier 2)
        flag_codes = [f.code for f in result.flags]
        assert "FORK_OF_POPULAR" in flag_codes
        assert result.plagiarism_detected is True
        assert result.score_adjustment < 0


@pytest.mark.asyncio
async def test_tier2_detects_bulk_upload():
    from app.services.tier2_verifier import Tier2Verifier

    # Mock for repo info (not a fork)
    repo_response = MagicMock()
    repo_response.status_code = 200
    repo_response.json.return_value = {"fork": False, "name": "my-project"}

    # Mock for commits list
    commits_response = MagicMock()
    commits_response.status_code = 200
    commits_response.json.return_value = [
        {"sha": "abc123", "commit": {"author": {"date": "2024-01-01T10:00:00Z"}}}
    ]

    # Mock for commit details - bulk upload
    commit_detail_response = MagicMock()
    commit_detail_response.status_code = 200
    commit_detail_response.json.return_value = {
        "stats": {"additions": 10000, "deletions": 0},
        "files": [{"filename": f"file{i}.py"} for i in range(30)]
    }

    call_count = [0]

    def mock_get(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        call_count[0] += 1

        if "/commits?" in url:
            return commits_response
        elif "/commits/" in url:
            return commit_detail_response
        else:
            return repo_response

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(side_effect=mock_get)
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClient.return_value = mock_instance

        verifier = Tier2Verifier(github_token="fake")
        result = await verifier.analyze(owner="user", repo="project", github_username="user")

        flag_codes = [f.code for f in result.flags]
        assert "BULK_INITIAL_COMMIT" in flag_codes
        assert result.plagiarism_detected is True


@pytest.mark.asyncio
async def test_tier2_detects_tutorial_keywords():
    from app.services.tier2_verifier import Tier2Verifier

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "fork": False,
        "name": "react-tutorial-project",
        "description": "My bootcamp assignment for learning React"
    }

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClient.return_value = mock_instance

        verifier = Tier2Verifier(github_token="fake")
        result = await verifier.analyze(owner="user", repo="tutorial-project", github_username="user")

        flag_codes = [f.code for f in result.flags]
        assert "TUTORIAL_INDICATORS" in flag_codes


@pytest.mark.asyncio
async def test_tier2_clean_repo_no_flags():
    from app.services.tier2_verifier import Tier2Verifier

    # Mock for clean original repo
    repo_response = MagicMock()
    repo_response.status_code = 200
    repo_response.json.return_value = {
        "fork": False,
        "name": "my-awesome-app",
        "description": "A productivity app I built"
    }

    # Multiple commits spread over time
    commits_response = MagicMock()
    commits_response.status_code = 200
    commits_response.json.return_value = [
        {"sha": f"sha{i}", "commit": {"author": {"date": f"2024-01-{i+1:02d}T10:00:00Z"}}}
        for i in range(20)
    ]

    # Normal first commit
    commit_detail_response = MagicMock()
    commit_detail_response.status_code = 200
    commit_detail_response.json.return_value = {
        "stats": {"additions": 100, "deletions": 0},
        "files": [{"filename": "main.py"}, {"filename": "README.md"}]
    }

    def mock_get(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        if "/commits?" in url:
            return commits_response
        elif "/commits/" in url:
            return commit_detail_response
        else:
            return repo_response

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(side_effect=mock_get)
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClient.return_value = mock_instance

        verifier = Tier2Verifier(github_token="fake")
        result = await verifier.analyze(owner="user", repo="my-app", github_username="user")

        # Clean repo should have no negative flags
        assert result.plagiarism_detected is False
        assert result.score_adjustment == 0
