from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
import httpx


@dataclass
class Flag:
    type: str  # "positive" or "negative"
    code: str
    message: str


@dataclass
class Tier2Result:
    score_adjustment: int = 0
    plagiarism_detected: bool = False
    flags: list[Flag] = field(default_factory=list)
    analysis_notes: list[str] = field(default_factory=list)


class Tier2Verifier:
    """
    Tier 2 verification using GitHub signals to detect plagiarism.
    No external API keys required - uses only GitHub data.
    """

    KNOWN_TUTORIAL_REPOS = [
        "facebook/react",
        "tastejs/todomvc",
        "gothinkster/realworld",
        "django/django",
        "pallets/flask",
        "tiangolo/fastapi",
        "expressjs/express",
        "spring-projects/spring-petclinic",
    ]

    def __init__(
        self,
        github_client=None,
        fingerprint_matcher=None,
        github_token: str = "",
        openai_api_key: str = "",
        anthropic_api_key: str = "",
    ):
        self.github_client = github_client
        self.github_token = github_token or (github_client.token if github_client else "")
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
        }

    async def analyze(
        self,
        repo_url: str = "",
        github_username: str = "",
        owner: str = "",
        repo: str = "",
    ) -> Tier2Result:
        """Run Tier 2 analysis using GitHub signals."""

        # Parse owner/repo from URL if provided
        if repo_url and not (owner and repo):
            from urllib.parse import urlparse
            parsed = urlparse(repo_url)
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]

        result = Tier2Result()

        if not owner or not repo:
            result.analysis_notes.append("Could not parse repository")
            return result

        # Run all checks
        await self._check_fork_status(owner, repo, result)
        await self._check_commit_patterns(owner, repo, github_username, result)
        await self._check_bulk_upload(owner, repo, github_username, result)
        await self._check_known_tutorial_fork(owner, repo, result)

        return result

    async def _request(self, url: str) -> Optional[dict]:
        """Make a GitHub API request."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def _check_fork_status(self, owner: str, repo: str, result: Tier2Result):
        """Check if repo is a fork and analyze parent."""
        data = await self._request(f"https://api.github.com/repos/{owner}/{repo}")
        if not data:
            return

        if data.get("fork"):
            parent = data.get("parent", {})
            parent_name = parent.get("full_name", "unknown")
            parent_stars = parent.get("stargazers_count", 0)

            # Note: IS_FORK flag is added by Tier 1, so we don't duplicate it here
            result.analysis_notes.append(f"Forked from {parent_name} ({parent_stars} stars)")

            # Check if parent is a popular tutorial/template
            if parent_stars > 1000:
                result.flags.append(Flag(
                    type="negative",
                    code="FORK_OF_POPULAR",
                    message=f"Fork of popular repo with {parent_stars} stars"
                ))
                result.score_adjustment -= 15
                result.plagiarism_detected = True

    async def _check_commit_patterns(self, owner: str, repo: str, username: str, result: Tier2Result):
        """Analyze commit timing patterns."""
        data = await self._request(
            f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
        )
        if not data or not isinstance(data, list):
            return

        if len(data) == 0:
            return

        # Get commit dates
        dates = []
        for commit in data:
            commit_data = commit.get("commit", {})
            author_data = commit_data.get("author", {})
            date_str = author_data.get("date", "")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    dates.append(dt)
                except:
                    pass

        if len(dates) < 2:
            return

        # Check 1: All commits in one day
        dates.sort()
        total_span = (dates[-1] - dates[0]).days

        if total_span == 0 and len(dates) >= 5:
            result.flags.append(Flag(
                type="negative",
                code="SINGLE_DAY_COMMITS",
                message=f"All {len(dates)} commits made in a single day"
            ))
            result.score_adjustment -= 15
            result.analysis_notes.append("Suspicious: entire project committed in one day")

        # Check 2: Rapid burst commits (many commits in minutes)
        burst_count = 0
        for i in range(1, len(dates)):
            diff = (dates[i] - dates[i-1]).total_seconds()
            if diff < 60:  # Less than 1 minute between commits
                burst_count += 1

        if burst_count > len(dates) * 0.5:
            result.flags.append(Flag(
                type="negative",
                code="BURST_COMMITS",
                message="Many commits made within seconds of each other"
            ))
            result.score_adjustment -= 10
            result.analysis_notes.append("Commits suggest automated or bulk upload")

    async def _check_bulk_upload(self, owner: str, repo: str, username: str, result: Tier2Result):
        """Check for bulk code upload patterns."""
        # Get first commit to check if it added many files
        data = await self._request(
            f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
        )
        if not data or not isinstance(data, list) or len(data) == 0:
            return

        # Get the first (oldest) commit details
        first_commit_sha = data[-1].get("sha", "")
        if not first_commit_sha:
            return

        commit_data = await self._request(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{first_commit_sha}"
        )
        if not commit_data:
            return

        stats = commit_data.get("stats", {})
        files = commit_data.get("files", [])
        additions = stats.get("additions", 0)

        # Red flag: First commit adds massive amount of code
        if additions > 5000 and len(files) > 20:
            result.flags.append(Flag(
                type="negative",
                code="BULK_INITIAL_COMMIT",
                message=f"First commit added {additions} lines across {len(files)} files"
            ))
            result.score_adjustment -= 20
            result.plagiarism_detected = True
            result.analysis_notes.append("Project appears to be bulk uploaded, not developed incrementally")

        # Also suspicious: Very few commits for large project
        total_commits = len(data)
        if total_commits <= 3 and additions > 2000:
            result.flags.append(Flag(
                type="negative",
                code="FEW_COMMITS_LARGE_PROJECT",
                message=f"Only {total_commits} commits for {additions}+ lines of code"
            ))
            result.score_adjustment -= 10
            result.analysis_notes.append("Commit history doesn't reflect incremental development")

    async def _check_known_tutorial_fork(self, owner: str, repo: str, result: Tier2Result):
        """Check if repo is related to known tutorial repositories."""
        data = await self._request(f"https://api.github.com/repos/{owner}/{repo}")
        if not data:
            return

        # Check repo name for tutorial indicators
        repo_name = data.get("name", "").lower()
        description = (data.get("description") or "").lower()

        tutorial_keywords = [
            "tutorial", "bootcamp", "course", "exercise", "assignment",
            "homework", "lesson", "learning", "practice", "demo", "example",
            "starter", "template", "boilerplate", "clone"
        ]

        matched_keywords = [kw for kw in tutorial_keywords if kw in repo_name or kw in description]

        if matched_keywords:
            result.flags.append(Flag(
                type="negative",
                code="TUTORIAL_INDICATORS",
                message=f"Repo name/description contains: {', '.join(matched_keywords)}"
            ))
            result.score_adjustment -= 5
            result.analysis_notes.append(f"Tutorial-related keywords found: {matched_keywords}")

        # Check if this is a fork chain (fork of a fork)
        if data.get("fork"):
            parent = data.get("parent", {})
            if parent.get("fork"):
                result.flags.append(Flag(
                    type="negative",
                    code="FORK_OF_FORK",
                    message="Repository is a fork of another fork"
                ))
                result.score_adjustment -= 10
                result.analysis_notes.append("Fork chain detected - likely copied from tutorial")
