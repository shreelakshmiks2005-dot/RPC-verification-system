# Project Verification API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a REST API that verifies whether a candidate genuinely contributed to a GitHub project, returning a score (0-100), status, and specific flags.

**Architecture:** Two-tier verification system. Tier 1 runs synchronously (2-5s) using GitHub API signals. Tier 2 runs asynchronously via Celery for suspicious cases, using code embeddings and LLM analysis. PostgreSQL stores results; Redis queues background jobs.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, PostgreSQL, Redis, Celery, httpx (async GitHub API), OpenAI API (embeddings), Anthropic API (Claude analysis), Pydantic v2, SQLAlchemy 2.0, Alembic.

**Spec:** `docs/specs/2026-11-03-project-verification-design.md`

## Global Constraints

- Python 3.11+ required
- All API responses must be JSON with consistent error format
- GitHub API calls must have 10s timeout and 3 retries with exponential backoff
- Never block API response on Tier 2 analysis
- All timestamps in ISO 8601 UTC format
- Verification IDs use `ver_` prefix with UUID

## Review Focus

1. **Private/nonexistent repos** — API should return clear error, not crash, when repo is private or doesn't exist
2. **GitHub rate limiting** — Must handle 403 rate limit responses gracefully, return RATE_LIMITED error to client
3. **Malformed GitHub URLs** — URLs like `github.com/user` (no repo) or `gitlab.com/...` should return INVALID_URL
4. **Empty repos** — Repos with 0 commits should not crash scoring logic, should return low score with appropriate flag
5. **Username case sensitivity** — GitHub usernames are case-insensitive; `Lakshmi22` should match `lakshmi22` in contributor list

---

## File Structure

```
project-verification/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, routes
│   ├── config.py                  # Settings from env vars
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy engine, session
│   │   ├── verification.py        # Verification ORM model
│   │   └── fingerprint.py         # TutorialFingerprint ORM model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── verification.py        # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_client.py       # GitHub API wrapper
│   │   ├── tier1_verifier.py      # Tier 1 scoring logic
│   │   ├── tier2_verifier.py      # Tier 2 AI analysis
│   │   └── scoring.py             # Score calculation, status determination
│   └── workers/
│       ├── __init__.py
│       └── celery_app.py          # Celery config and tasks
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures
│   ├── test_github_client.py
│   ├── test_tier1_verifier.py
│   ├── test_scoring.py
│   ├── test_api.py
│   └── test_tier2_verifier.py
├── alembic/
│   └── versions/                  # DB migrations
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

### Task 1: Project Setup and Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/main.py`

**Interfaces:**
- Consumes: None (first task)
- Produces: `Settings` class with `database_url`, `redis_url`, `github_token`, `openai_api_key`, `anthropic_api_key` properties; `app` FastAPI instance; `/health` endpoint

- [ ] **Step 1: Create `pyproject.toml` with project metadata**

```toml
[project]
name = "project-verification"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "celery[redis]>=5.3.0",
    "openai>=1.10.0",
    "anthropic>=0.18.0",
]
```

- [ ] **Step 2: Create `requirements.txt`**

Same dependencies as pyproject.toml for pip compatibility.

- [ ] **Step 3: Create `.env.example`**

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/project_verification
REDIS_URL=redis://localhost:6379
GITHUB_TOKEN=ghp_xxxx
OPENAI_API_KEY=sk-xxxx
ANTHROPIC_API_KEY=sk-ant-xxxx
LOG_LEVEL=INFO
```

- [ ] **Step 4: Write failing test for config loading**

```python
# tests/test_config.py
def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    from app.config import Settings
    settings = Settings()
    assert settings.database_url == "postgresql+asyncpg://test"
    assert settings.github_token == "ghp_test"
```

- [ ] **Step 5: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with import error

- [ ] **Step 6: Implement `Settings` class in `app/config.py`**

Use pydantic-settings `BaseSettings` to load from environment variables with validation.

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 8: Write failing test for health endpoint**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

def test_health_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 9: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_health_returns_ok -v`
Expected: FAIL

- [ ] **Step 10: Implement `app/main.py` with FastAPI app and `/health` endpoint**

Create FastAPI app instance. Add GET `/health` returning `{"status": "ok", "version": "1.0.0"}`.

- [ ] **Step 11: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_health_returns_ok -v`
Expected: PASS

- [ ] **Step 12: Commit**

```bash
git init
git add .
git commit -m "feat: project setup with config and health endpoint"
```

---

### Task 2: Database Models and Schema

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/database.py`
- Create: `app/models/verification.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/001_initial.py`

**Interfaces:**
- Consumes: `Settings.database_url` from Task 1
- Produces: `Verification` model with fields: `id` (UUID), `candidate_id`, `candidate_name`, `github_username`, `repo_link`, `project_type`, `score`, `status`, `tier1_complete`, `tier2_complete`, `flags` (JSONB), `details` (JSONB), `created_at`, `updated_at`; `get_async_session()` dependency; `AsyncSessionLocal` factory

- [ ] **Step 1: Write failing test for Verification model**

```python
# tests/test_models.py
from app.models.verification import Verification
import uuid

def test_verification_model_has_required_fields():
    v = Verification(
        id=uuid.uuid4(),
        candidate_id="123",
        candidate_name="Test",
        github_username="testuser",
        repo_link="https://github.com/test/repo",
        project_type="individual",
        score=75,
        status="verified"
    )
    assert v.candidate_id == "123"
    assert v.status == "verified"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Implement `app/models/database.py`**

Create async SQLAlchemy engine from `Settings.database_url`. Create `AsyncSessionLocal` session factory. Create `get_async_session` dependency.

- [ ] **Step 4: Implement `app/models/verification.py`**

SQLAlchemy 2.0 model with all fields from spec. Use `Mapped` type hints. JSONB for `flags` and `details`. Enum for `status` and `project_type`.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 6: Initialize Alembic and create initial migration**

```bash
alembic init alembic
# Edit alembic/env.py to use async and import models
alembic revision --autogenerate -m "initial schema"
```

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: database models and migrations"
```

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/verification.py`

**Interfaces:**
- Consumes: None
- Produces: `VerificationRequest` (candidate_id, candidate_name, github_username, repo_link, project_type), `VerificationResponse` (all response fields from spec), `FlagSchema` (type, code, message), `ErrorResponse` (error, code, message)

- [ ] **Step 1: Write failing test for request validation**

```python
# tests/test_schemas.py
from app.schemas.verification import VerificationRequest
import pytest
from pydantic import ValidationError

def test_verification_request_validates_github_url():
    with pytest.raises(ValidationError):
        VerificationRequest(
            candidate_id="123",
            candidate_name="Test",
            github_username="user",
            repo_link="not-a-github-url",
            project_type="individual"
        )

def test_verification_request_accepts_valid_url():
    req = VerificationRequest(
        candidate_id="123",
        candidate_name="Test",
        github_username="user",
        repo_link="https://github.com/owner/repo",
        project_type="individual"
    )
    assert req.repo_link == "https://github.com/owner/repo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_schemas.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `app/schemas/verification.py`**

Pydantic v2 models. `VerificationRequest` with URL validator for `repo_link` (must be github.com). `VerificationResponse` with all fields. `FlagSchema` for flags array. `ErrorResponse` for errors.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: pydantic request/response schemas"
```

---

### Task 4: GitHub API Client

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/github_client.py`
- Create: `tests/test_github_client.py`

**Interfaces:**
- Consumes: `Settings.github_token` from Task 1
- Produces: `GitHubClient` class with methods: `get_repo(owner: str, repo: str) -> RepoData`, `get_contributors(owner: str, repo: str) -> list[Contributor]`, `get_commits(owner: str, repo: str, author: str | None) -> list[Commit]`, `get_pull_requests(owner: str, repo: str, author: str) -> list[PullRequest]`, `parse_repo_url(url: str) -> tuple[str, str]`

- [ ] **Step 1: Write failing test for URL parsing**

```python
# tests/test_github_client.py
from app.services.github_client import GitHubClient

def test_parse_repo_url_extracts_owner_and_repo():
    client = GitHubClient(token="fake")
    owner, repo = client.parse_repo_url("https://github.com/rahuldev/ai-project")
    assert owner == "rahuldev"
    assert repo == "ai-project"

def test_parse_repo_url_handles_trailing_slash():
    client = GitHubClient(token="fake")
    owner, repo = client.parse_repo_url("https://github.com/rahuldev/ai-project/")
    assert owner == "rahuldev"
    assert repo == "ai-project"

def test_parse_repo_url_raises_on_invalid():
    client = GitHubClient(token="fake")
    import pytest
    with pytest.raises(ValueError):
        client.parse_repo_url("https://gitlab.com/user/repo")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_github_client.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `GitHubClient.parse_repo_url(url: str) -> tuple[str, str]`**

Parse URL, validate github.com host, extract owner and repo from path. Raise ValueError on invalid URLs.

- [ ] **Step 4: Run URL parsing tests to verify they pass**

Run: `pytest tests/test_github_client.py::test_parse_repo_url* -v`
Expected: PASS

- [ ] **Step 5: Write failing test for get_repo with mock**

```python
# tests/test_github_client.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_get_repo_returns_repo_data():
    mock_response = {
        "fork": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-06-01T00:00:00Z",
        "stargazers_count": 10,
        "owner": {"login": "rahuldev"}
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        client = GitHubClient(token="fake")
        data = await client.get_repo("rahuldev", "ai-project")
        assert data.is_fork == False
        assert data.owner == "rahuldev"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_github_client.py::test_get_repo_returns_repo_data -v`
Expected: FAIL

- [ ] **Step 7: Implement `GitHubClient` with httpx async client**

Use httpx.AsyncClient with timeout=10s. Add retry logic with exponential backoff (3 retries). Handle 404 (RepoNotFoundError), 403 rate limit (RateLimitError). Implement `get_repo`, `get_contributors`, `get_commits`, `get_pull_requests`.

- [ ] **Step 8: Run all GitHub client tests**

Run: `pytest tests/test_github_client.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: github API client with retry and error handling"
```

---

### Task 5: Tier 1 Verification Logic

**Files:**
- Create: `app/services/tier1_verifier.py`
- Create: `app/services/scoring.py`
- Create: `tests/test_tier1_verifier.py`
- Create: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `GitHubClient` from Task 4, `RepoData`, `Contributor`, `Commit` types
- Produces: `Tier1Verifier.verify(github_username: str, repo_url: str, project_type: str) -> Tier1Result`, `calculate_score(checks: list[Check]) -> int`, `determine_status(score: int) -> str`

- [ ] **Step 1: Write failing test for score calculation**

```python
# tests/test_scoring.py
from app.services.scoring import calculate_score, determine_status

def test_calculate_score_sums_positive_checks():
    checks = [
        {"name": "is_owner", "points": 30, "passed": True},
        {"name": "is_contributor", "points": 25, "passed": True},
    ]
    assert calculate_score(checks) == 55

def test_calculate_score_subtracts_negative_flags():
    checks = [
        {"name": "is_contributor", "points": 25, "passed": True},
        {"name": "all_commits_one_day", "points": -20, "passed": True},
    ]
    assert calculate_score(checks) == 5

def test_determine_status_verified():
    assert determine_status(75) == "verified"
    assert determine_status(100) == "verified"

def test_determine_status_needs_review():
    assert determine_status(45) == "needs_review"
    assert determine_status(74) == "needs_review"

def test_determine_status_suspicious():
    assert determine_status(44) == "suspicious"
    assert determine_status(0) == "suspicious"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scoring.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `app/services/scoring.py`**

`calculate_score(checks)` sums points where passed=True, clamps to 0-100. `determine_status(score)` returns "verified" (≥75), "needs_review" (45-74), "suspicious" (<45).

- [ ] **Step 4: Run scoring tests to verify they pass**

Run: `pytest tests/test_scoring.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for Tier1Verifier**

```python
# tests/test_tier1_verifier.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.tier1_verifier import Tier1Verifier

@pytest.mark.asyncio
async def test_tier1_verifier_owner_gets_points():
    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("lakshmi22", "my-project")
    mock_client.get_repo = AsyncMock(return_value=MagicMock(
        owner="lakshmi22", is_fork=False
    ))
    mock_client.get_contributors = AsyncMock(return_value=[
        MagicMock(login="lakshmi22", contributions=10)
    ])
    mock_client.get_commits = AsyncMock(return_value=[
        MagicMock(author="lakshmi22", date="2024-01-01") for _ in range(10)
    ])
    
    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="lakshmi22",
        repo_url="https://github.com/lakshmi22/my-project",
        project_type="individual"
    )
    
    assert result.score >= 75  # Owner + contributor + commits
    assert any(f.code == "IS_OWNER" for f in result.flags if f.type == "positive")
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_tier1_verifier.py -v`
Expected: FAIL

- [ ] **Step 7: Implement `Tier1Verifier` in `app/services/tier1_verifier.py`**

Implement all Layer 1-4 checks from spec:
- Layer 1: is_owner (+30), is_contributor (+25), commit_count (+20 if ≥5), code_files_touched (+15), lines_of_code (+10 if ≥100)
- Layer 2: commit_spread (+10 if ≥7 days), no_burst (+5), recent_activity (+5)
- Layer 2 red flags: all_commits_one_day (-20), ancient_untouched (-10)
- Layer 3: pr_participation (+10), issue_participation (+5), multiple_contributors (+5)
- Layer 3 red flags: solo_group_project (-15), coattail_riding (-20)
- Layer 4: fork_of_tutorial (-30), very_low_contribution (-15), only_docs (-10)

Return `Tier1Result` with score, status, flags, details.

- [ ] **Step 8: Run all Tier 1 tests**

Run: `pytest tests/test_tier1_verifier.py -v`
Expected: PASS

- [ ] **Step 9: Add test for case-insensitive username matching**

```python
@pytest.mark.asyncio
async def test_tier1_verifier_matches_username_case_insensitive():
    mock_client = MagicMock()
    mock_client.parse_repo_url.return_value = ("owner", "repo")
    mock_client.get_repo = AsyncMock(return_value=MagicMock(owner="Owner", is_fork=False))
    mock_client.get_contributors = AsyncMock(return_value=[
        MagicMock(login="LAKSHMI22", contributions=10)
    ])
    mock_client.get_commits = AsyncMock(return_value=[])
    
    verifier = Tier1Verifier(mock_client)
    result = await verifier.verify(
        github_username="lakshmi22",  # lowercase
        repo_url="https://github.com/owner/repo",
        project_type="individual"
    )
    
    assert any(f.code == "IS_CONTRIBUTOR" for f in result.flags if f.type == "positive")
```

- [ ] **Step 10: Run test and ensure it passes**

Run: `pytest tests/test_tier1_verifier.py::test_tier1_verifier_matches_username_case_insensitive -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add .
git commit -m "feat: tier 1 verification with all scoring layers"
```

---

### Task 6: API Endpoints

**Files:**
- Modify: `app/main.py`
- Create: `tests/test_api.py` (expand)

**Interfaces:**
- Consumes: `VerificationRequest`, `VerificationResponse` from Task 3, `Verification` model from Task 2, `Tier1Verifier` from Task 5, `get_async_session` from Task 2
- Produces: `POST /verify-project` endpoint, `GET /verify-project/{verification_id}` endpoint

- [ ] **Step 1: Write failing test for POST /verify-project**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

def test_verify_project_returns_verification_response():
    mock_result = MagicMock(
        score=82,
        status="verified",
        flags=[],
        details={"owner": "testuser", "candidate_commits": 10}
    )
    
    with patch("app.main.Tier1Verifier") as MockVerifier:
        MockVerifier.return_value.verify = AsyncMock(return_value=mock_result)
        
        client = TestClient(app)
        response = client.post("/verify-project", json={
            "candidate_id": "123",
            "candidate_name": "Test User",
            "github_username": "testuser",
            "repo_link": "https://github.com/testuser/myrepo",
            "project_type": "individual"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 82
        assert data["status"] == "verified"
        assert data["verification_id"].startswith("ver_")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_verify_project_returns_verification_response -v`
Expected: FAIL

- [ ] **Step 3: Implement POST /verify-project in `app/main.py`**

Accept `VerificationRequest`. Call `Tier1Verifier.verify()`. Generate `ver_` UUID. Save to database. Return `VerificationResponse`. Queue Tier 2 job if score < 75.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_verify_project_returns_verification_response -v`
Expected: PASS

- [ ] **Step 5: Write failing test for GET /verify-project/{id}**

```python
def test_get_verification_returns_stored_result():
    # First create a verification, then retrieve it
    # ... setup mock ...
    client = TestClient(app)
    response = client.get("/verify-project/ver_nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 6: Implement GET /verify-project/{verification_id}**

Query database by ID. Return 404 if not found. Return `VerificationResponse` with current state.

- [ ] **Step 7: Run all API tests**

Run: `pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 8: Write test for error handling (invalid URL)**

```python
def test_verify_project_rejects_invalid_github_url():
    client = TestClient(app)
    response = client.post("/verify-project", json={
        "candidate_id": "123",
        "candidate_name": "Test",
        "github_username": "user",
        "repo_link": "https://gitlab.com/user/repo",
        "project_type": "individual"
    })
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_URL"
```

- [ ] **Step 9: Run test and ensure it passes**

Run: `pytest tests/test_api.py::test_verify_project_rejects_invalid_github_url -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add .
git commit -m "feat: POST and GET /verify-project endpoints"
```

---

### Task 7: Celery Worker and Tier 2 Infrastructure

**Files:**
- Create: `app/workers/__init__.py`
- Create: `app/workers/celery_app.py`
- Create: `app/services/tier2_verifier.py`
- Create: `tests/test_tier2_verifier.py`

**Interfaces:**
- Consumes: `Settings.redis_url`, `Settings.openai_api_key`, `Settings.anthropic_api_key` from Task 1, `Verification` model from Task 2
- Produces: `celery_app` Celery instance, `run_tier2_analysis` task, `Tier2Verifier.analyze(repo_url: str, github_username: str) -> Tier2Result`

- [ ] **Step 1: Write failing test for Celery task registration**

```python
# tests/test_celery.py
def test_tier2_task_is_registered():
    from app.workers.celery_app import celery_app
    assert "run_tier2_analysis" in celery_app.tasks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_celery.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `app/workers/celery_app.py`**

Create Celery app with Redis broker from settings. Define `run_tier2_analysis(verification_id: str)` task that loads verification, runs Tier 2 analysis, updates database.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_celery.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for Tier2Verifier code download**

```python
# tests/test_tier2_verifier.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_tier2_downloads_repo_files():
    with patch("app.services.tier2_verifier.httpx.AsyncClient") as MockClient:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tree": [
                {"path": "main.py", "type": "blob", "size": 1000},
                {"path": "README.md", "type": "blob", "size": 500},
            ]
        }
        MockClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        from app.services.tier2_verifier import Tier2Verifier
        verifier = Tier2Verifier(github_token="fake", openai_key="fake", anthropic_key="fake")
        files = await verifier.get_code_files("owner", "repo")
        
        assert len(files) == 1  # Only .py, not .md
        assert files[0]["path"] == "main.py"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_tier2_verifier.py -v`
Expected: FAIL

- [ ] **Step 7: Implement `Tier2Verifier` in `app/services/tier2_verifier.py`**

Implement `get_code_files(owner, repo)` to fetch file tree, filter to code files only (.py, .js, .ts, .java, .go, .rs, etc.), respect 100MB limit. Implement `generate_embeddings(code: str)` using OpenAI API. Implement `analyze_with_llm(code: str, context: str)` using Claude API.

- [ ] **Step 8: Run all Tier 2 tests**

Run: `pytest tests/test_tier2_verifier.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add .
git commit -m "feat: celery worker and tier 2 analysis infrastructure"
```

---

### Task 8: Tutorial Fingerprint Database

**Files:**
- Create: `app/models/fingerprint.py`
- Create: `app/services/fingerprint_matcher.py`
- Create: `alembic/versions/002_fingerprints.py`
- Create: `scripts/seed_fingerprints.py`
- Create: `tests/test_fingerprint_matcher.py`

**Interfaces:**
- Consumes: `AsyncSessionLocal` from Task 2
- Produces: `TutorialFingerprint` model, `FingerprintMatcher.check_similarity(code_hash: str, embedding: list[float]) -> list[Match]`

- [ ] **Step 1: Write failing test for fingerprint model**

```python
# tests/test_fingerprint_matcher.py
from app.models.fingerprint import TutorialFingerprint

def test_fingerprint_model_has_required_fields():
    fp = TutorialFingerprint(
        source_name="freeCodeCamp React Tutorial",
        source_url="https://github.com/freeCodeCamp/...",
        file_hashes={"main.js": "abc123"},
    )
    assert fp.source_name == "freeCodeCamp React Tutorial"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fingerprint_matcher.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `TutorialFingerprint` model**

SQLAlchemy model with `id`, `source_name`, `source_url`, `file_hashes` (JSONB), `embedding` (for future vector similarity), `created_at`.

- [ ] **Step 4: Create migration for fingerprints table**

```bash
alembic revision --autogenerate -m "add fingerprints table"
```

- [ ] **Step 5: Implement `FingerprintMatcher` in `app/services/fingerprint_matcher.py`**

`check_hash_match(file_hashes: dict)` compares against stored hashes. Returns matches with similarity percentage.

- [ ] **Step 6: Create seed script with initial tutorial fingerprints**

Add 10-20 popular tutorial repos: freeCodeCamp projects, common Udemy course repos, popular bootcamp templates.

- [ ] **Step 7: Run all fingerprint tests**

Run: `pytest tests/test_fingerprint_matcher.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: tutorial fingerprint database and matching"
```

---

### Task 9: Integration and End-to-End Testing

**Files:**
- Modify: `app/main.py` (wire everything together)
- Create: `tests/test_integration.py`
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Fully integrated API, docker-compose for local development

- [ ] **Step 1: Create docker-compose.yml**

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: project_verification
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

- [ ] **Step 2: Write integration test with real HTTP calls**

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.integration
def test_full_verification_flow():
    client = TestClient(app)
    
    # Submit verification
    response = client.post("/verify-project", json={
        "candidate_id": "integration-test",
        "candidate_name": "Test User",
        "github_username": "octocat",
        "repo_link": "https://github.com/octocat/Hello-World",
        "project_type": "individual"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "verification_id" in data
    assert data["tier1_complete"] == True
    
    # Retrieve verification
    ver_id = data["verification_id"]
    response = client.get(f"/verify-project/{ver_id}")
    assert response.status_code == 200
    assert response.json()["verification_id"] == ver_id
```

- [ ] **Step 3: Run integration tests**

Run: `docker-compose up -d && pytest tests/test_integration.py -v -m integration`
Expected: PASS

- [ ] **Step 4: Wire up health check to include DB and Redis status**

Modify `/health` to check database connection and Redis connection, return status for each.

- [ ] **Step 5: Run full test suite**

Run: `pytest --cov=app tests/ -v`
Expected: All tests PASS, coverage > 80%

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: integration tests and docker-compose"
```

---

### Task 10: Production Deployment Configuration

**Files:**
- Create: `Dockerfile`
- Create: `Procfile` (for Railway/Render)
- Create: `railway.toml` or `render.yaml`
- Create: `README.md`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Deployable application with documentation

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create Procfile**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.workers.celery_app worker --loglevel=info
```

- [ ] **Step 3: Build and test Docker image locally**

```bash
docker build -t project-verification .
docker run -p 8000:8000 --env-file .env project-verification
curl http://localhost:8000/health
```
Expected: `{"status": "ok"}`

- [ ] **Step 4: Create README.md with setup instructions**

Document: project overview, local setup, environment variables, API endpoints, deployment instructions.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: production deployment configuration"
```

---

## Summary

| Task | Deliverable | Tests |
|------|-------------|-------|
| 1 | Project setup, config, health endpoint | Config loading, health check |
| 2 | Database models, migrations | Model field validation |
| 3 | Pydantic schemas | URL validation, required fields |
| 4 | GitHub API client | URL parsing, API calls with mocks |
| 5 | Tier 1 verification logic | Scoring, status, all check layers |
| 6 | API endpoints | POST/GET endpoints, error handling |
| 7 | Celery + Tier 2 infrastructure | Task registration, code download |
| 8 | Fingerprint database | Model, matching, seed data |
| 9 | Integration testing | End-to-end flow |
| 10 | Deployment config | Docker, Procfile, docs |

**Total: 10 tasks, approximately 3 weeks to complete**
