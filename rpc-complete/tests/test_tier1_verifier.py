import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MockRepoData:
    owner: str
    name: str = "test-repo"
    is_fork: bool = False
    created_at: str = "2024-01-01T00:00:00Z"
    updated_at: str = "2024-06-01T00:00:00Z"
    stars: int = 10
    parent_url: str = None


@dataclass
class MockContributor:
    login: str
    contributions: int


@dataclass
class MockCommit:
    sha: str
    author: str
    date: str
    message: str
    additions: int = 100
    deletions: int = 10
    files_changed: list = None

    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = ["main.py"]


@pytest.mark.asyncio
async def test_tier1_verifier_owner_gets_points():
    from app.services.tier1_verifier import Tier1Verifier

    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("lakshmi22", "my-project")
    mock_client.get_repo = AsyncMock(
        return_value=MockRepoData(owner="lakshmi22", is_fork=False)
    )
    mock_client.get_contributors = AsyncMock(
        return_value=[MockContributor(login="lakshmi22", contributions=10)]
    )
    mock_client.get_commits = AsyncMock(
        return_value=[
            MockCommit(sha=f"abc{i}", author="lakshmi22", date="2024-01-15T00:00:00Z", message="commit")
            for i in range(10)
        ]
    )
    mock_client.get_pull_requests = AsyncMock(return_value=[])

    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="lakshmi22",
        repo_url="https://github.com/lakshmi22/my-project",
        project_type="individual",
    )

    assert result.score >= 75
    assert any(f.code == "IS_OWNER" for f in result.flags if f.type == "positive")


@pytest.mark.asyncio
async def test_tier1_verifier_non_contributor_gets_low_score():
    from app.services.tier1_verifier import Tier1Verifier

    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("otheruser", "project")
    mock_client.get_repo = AsyncMock(
        return_value=MockRepoData(owner="otheruser", is_fork=False)
    )
    mock_client.get_contributors = AsyncMock(
        return_value=[MockContributor(login="otheruser", contributions=50)]
    )
    mock_client.get_commits = AsyncMock(return_value=[])
    mock_client.get_pull_requests = AsyncMock(return_value=[])

    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="fakeuser",
        repo_url="https://github.com/otheruser/project",
        project_type="individual",
    )

    assert result.score < 45
    assert result.status == "suspicious"


@pytest.mark.asyncio
async def test_tier1_verifier_matches_username_case_insensitive():
    from app.services.tier1_verifier import Tier1Verifier

    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("owner", "repo")
    mock_client.get_repo = AsyncMock(
        return_value=MockRepoData(owner="Owner", is_fork=False)
    )
    mock_client.get_contributors = AsyncMock(
        return_value=[MockContributor(login="LAKSHMI22", contributions=10)]
    )
    mock_client.get_commits = AsyncMock(
        return_value=[
            MockCommit(sha="abc", author="LAKSHMI22", date="2024-01-01T00:00:00Z", message="commit")
        ]
    )
    mock_client.get_pull_requests = AsyncMock(return_value=[])

    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="lakshmi22",
        repo_url="https://github.com/owner/repo",
        project_type="individual",
    )

    assert any(f.code == "IS_CONTRIBUTOR" for f in result.flags if f.type == "positive")


@pytest.mark.asyncio
async def test_tier1_verifier_detects_fork():
    from app.services.tier1_verifier import Tier1Verifier

    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("user", "forked-repo")
    mock_client.get_repo = AsyncMock(
        return_value=MockRepoData(owner="user", is_fork=True, parent_url="https://github.com/original/repo")
    )
    mock_client.get_contributors = AsyncMock(
        return_value=[MockContributor(login="user", contributions=2)]
    )
    mock_client.get_commits = AsyncMock(
        return_value=[
            MockCommit(sha="abc", author="user", date="2024-01-01T00:00:00Z", message="commit")
        ]
    )
    mock_client.get_pull_requests = AsyncMock(return_value=[])

    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="user",
        repo_url="https://github.com/user/forked-repo",
        project_type="individual",
    )

    assert any(f.code == "IS_FORK" for f in result.flags if f.type == "negative")
