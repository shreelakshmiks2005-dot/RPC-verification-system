import httpx
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
import asyncio


class RepoNotFoundError(Exception):
    pass


class RateLimitError(Exception):
    pass


class InvalidUsernameError(Exception):
    pass


@dataclass
class RepoData:
    owner: str
    name: str
    is_fork: bool
    created_at: str
    updated_at: str
    stars: int
    parent_url: Optional[str] = None


@dataclass
class Contributor:
    login: str
    contributions: int


@dataclass
class Commit:
    sha: str
    author: Optional[str]
    date: str
    message: str
    additions: int = 0
    deletions: int = 0
    files_changed: list[str] = None

    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []


@dataclass
class PullRequest:
    number: int
    title: str
    state: str
    author: str
    created_at: str


class GitHubClient:
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10.0
    MAX_RETRIES = 3

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        parsed = urlparse(url.rstrip("/").removesuffix(".git"))
        if parsed.netloc not in ("github.com", "www.github.com"):
            raise ValueError(f"Invalid GitHub URL: {url}")

        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")

        return path_parts[0], path_parts[1]

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                    response = await client.request(
                        method, url, headers=self.headers, **kwargs
                    )

                    if response.status_code == 404:
                        raise RepoNotFoundError(f"Repository not found. If it's a private repo, make sure your GitHub token has the 'repo' scope.")
                    if response.status_code == 403:
                        data = response.json()
                        if "rate limit" in data.get("message", "").lower():
                            raise RateLimitError("GitHub API rate limit exceeded")
                        # Private repo or blocked access
                        raise RepoNotFoundError("Access denied. This may be a private repository — your GitHub token needs the 'repo' scope to access private repos.")
                    if response.status_code >= 400:
                        response.raise_for_status()

                    return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise Exception("Max retries exceeded")

    async def get_repo(self, owner: str, repo: str) -> RepoData:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = await self._request("GET", url)
        data = response.json()

        return RepoData(
            owner=data["owner"]["login"],
            name=data.get("name", repo),
            is_fork=data.get("fork", False),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            stars=data.get("stargazers_count", 0),
            parent_url=data.get("parent", {}).get("html_url") if data.get("fork") else None,
        )

    async def get_contributors(self, owner: str, repo: str) -> list[Contributor]:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
        response = await self._request("GET", url)

        # Empty repos return 204 No Content
        if response.status_code == 204:
            return []

        data = response.json()
        contributors = [
            Contributor(login=c["login"], contributions=c["contributions"])
            for c in data
            if isinstance(c, dict) and "login" in c
        ]

        # If GitHub returns empty list (unlinked git emails), fall back to building
        # contributor list from commit history using git author names
        if not contributors:
            commits = await self.get_commits(owner, repo)
            counts: dict[str, int] = {}
            for commit in commits:
                if commit.author:
                    counts[commit.author] = counts.get(commit.author, 0) + 1
            contributors = [
                Contributor(login=name, contributions=count)
                for name, count in sorted(counts.items(), key=lambda x: -x[1])
            ]

        return contributors

    async def get_commits(
        self, owner: str, repo: str, author: Optional[str] = None
    ) -> list[Commit]:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"per_page": 100}
        if author:
            params["author"] = author

        response = await self._request("GET", url, params=params)

        # Empty repos return 204 No Content or 409 Conflict
        if response.status_code in (204, 409):
            return []

        data = response.json()

        commits = []
        for c in data:
            if not isinstance(c, dict):
                continue
            commit_data = c.get("commit", {})
            author_data = commit_data.get("author", {})
            # GitHub login may be None when git email isn't linked to a GitHub account
            # Fall back to the git author name so tier1 can still match by name
            github_login = c.get("author", {}).get("login") if c.get("author") else None
            git_author_name = author_data.get("name", "")
            commits.append(
                Commit(
                    sha=c.get("sha", ""),
                    author=github_login or git_author_name or None,
                    date=author_data.get("date", ""),
                    message=commit_data.get("message", ""),
                )
            )
        return commits

    async def get_pull_requests(
        self, owner: str, repo: str, author: Optional[str] = None
    ) -> list[PullRequest]:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        params = {"state": "all", "per_page": 100}

        response = await self._request("GET", url, params=params)
        data = response.json()

        prs = []
        for pr in data:
            if not isinstance(pr, dict):
                continue
            pr_author = pr.get("user", {}).get("login", "")
            if author and pr_author.lower() != author.lower():
                continue
            prs.append(
                PullRequest(
                    number=pr.get("number", 0),
                    title=pr.get("title", ""),
                    state=pr.get("state", ""),
                    author=pr_author,
                    created_at=pr.get("created_at", ""),
                )
            )
        return prs

    async def check_user_exists(self, username: str) -> bool:
        url = f"{self.BASE_URL}/users/{username}"
        try:
            await self._request("GET", url)
            return True
        except RepoNotFoundError:
            return False

    async def get_user_profile(self, username: str) -> dict:
        """
        Returns account age, followers, public repos, bio, avatar status.
        Used for account age and profile completeness fraud checks.
        """
        url = f"{self.BASE_URL}/users/{username}"
        response = await self._request("GET", url)
        data = response.json()
        return {
            "login": data.get("login"),
            "created_at": data.get("created_at", ""),
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "bio": data.get("bio") or "",
            "has_avatar": not (data.get("avatar_url", "").endswith("identicons") or
                               "gravatar" in data.get("avatar_url", "")),
            "name": data.get("name") or "",
            "blog": data.get("blog") or "",
            "company": data.get("company") or "",
        }

    async def get_commit_detail(self, owner: str, repo: str, sha: str) -> dict:
        """
        Fetch a single commit's file stats: additions, deletions, files changed.
        Used for TOUCHED_CODE and lines_added checks.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}"
        try:
            response = await self._request("GET", url)
            data = response.json()
            stats = data.get("stats", {})
            files = data.get("files", [])
            # Separate committer date (when pushed) vs author date (what git recorded)
            commit_data = data.get("commit", {})
            author_date = commit_data.get("author", {}).get("date", "")
            committer_date = commit_data.get("committer", {}).get("date", "")
            return {
                "additions": stats.get("additions", 0),
                "deletions": stats.get("deletions", 0),
                "total": stats.get("total", 0),
                "files": [f.get("filename", "") for f in files],
                "author_date": author_date,
                "committer_date": committer_date,
            }
        except Exception:
            return {"additions": 0, "deletions": 0, "total": 0, "files": [],
                    "author_date": "", "committer_date": ""}
