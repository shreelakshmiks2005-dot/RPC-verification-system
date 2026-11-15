# Project Verification API — Design Document

## Overview

A REST API service that verifies whether a candidate genuinely contributed to a GitHub project they claim on their portfolio or resume. Part of a larger candidate verification system that includes certification verification and resume verification (handled by other team members).

### Why This Exists

Candidates often claim projects they didn't actually build — forked repos with minimal changes, tutorial copy-paste, riding on group project coattails. This API analyzes GitHub data and source code to produce a verification score and flag suspicious patterns.

### Integration Context

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (Team member)                 │
│         Unified candidate verification UI           │
└───────────┬─────────────┬─────────────┬─────────────┘
            │             │             │
            ▼             ▼             ▼
     ┌──────────┐  ┌──────────┐  ┌──────────────┐
     │  Cert    │  │  Resume  │  │   Project    │
     │  API     │  │  API     │  │   API        │
     │ (Team)   │  │ (Team)   │  │   (This doc) │
     └──────────┘  └──────────┘  └──────────────┘
```

This document covers **Project API** only.

---

## Goals

1. **Detect fake contributions** — candidates who claim projects they didn't build
2. **Provide evidence** — specific flags explaining why a submission is suspicious
3. **Integrate cleanly** — reliable API that the frontend can depend on
4. **24/7 availability** — always running, auto-recovers from failures

## Non-Goals

1. Building the frontend (handled by team member)
2. Certification or resume verification (handled by team members)
3. Detecting every possible form of fraud (diminishing returns)

## Anti-Goals

1. **False accusations** — flagging legitimate contributors as suspicious
2. **Blocking on AI analysis** — slow AI checks should not block the API response
3. **Single point of failure** — one component crash should not take down the system

---

## Architecture

### High-Level Flow

```
POST /verify-project
        │
        ▼
┌───────────────────┐
│   Input Validation │
│   (Pydantic)       │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  GitHub Data Fetch │
│  - Repo metadata   │
│  - Contributors    │
│  - Commits         │
│  - PRs & Issues    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Tier 1: Fast     │
│  Verification     │
│  (GitHub signals) │
└─────────┬─────────┘
          │
          ├─── Score ≥ 75 ──► Return "Verified"
          │
          ▼ Score < 75
┌───────────────────┐
│  Queue Tier 2     │
│  (Background)     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Return initial   │
│  score + "pending │
│  deep analysis"   │
└───────────────────┘

        ... Background worker ...

┌───────────────────┐
│  Tier 2: AI Deep  │
│  Analysis         │
│  - Code download  │
│  - Embeddings     │
│  - LLM analysis   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Update DB with   │
│  final score      │
└───────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Server | FastAPI + Uvicorn | REST endpoints, request handling |
| Database | PostgreSQL | Store verification results, tutorial fingerprints |
| Job Queue | Redis + Celery | Background AI analysis tasks |
| AI - Embeddings | OpenAI text-embedding-3-small | Code similarity detection |
| AI - Analysis | Claude API | Deep analysis of suspicious cases |
| Hosting | Railway / Render | 24/7 managed deployment |

---

## Verification Layers

### Tier 1: Fast Checks (Every Submission)

Runs synchronously, returns in 2-5 seconds.

#### Layer 1: Contribution Reality

| Check | Points | Condition |
|-------|--------|-----------|
| Is owner | +30 | repo owner == candidate username |
| Is contributor | +25 | candidate in contributors list |
| Commit count | +20 | commits ≥ 5 |
| Code files touched | +15 | touched .py/.js/.java/etc, not just .md |
| Lines of code | +10 | added ≥ 100 lines of actual code |

#### Layer 2: Timing Patterns

| Check | Points | Condition |
|-------|--------|-----------|
| Commit spread | +10 | first-to-last commit span ≥ 7 days |
| No burst | +5 | less than 80% commits in single 24h window |
| Recent activity | +5 | last commit within 6 months |

**Red flags (negative points):**

| Flag | Points | Condition |
|------|--------|-----------|
| All commits in 1 day | -20 | 100% commits within 24 hours |
| Ancient & untouched | -10 | no commits in 2+ years |

#### Layer 3: Collaboration Depth (Group Projects)

| Check | Points | Condition |
|-------|--------|-----------|
| PR participation | +10 | opened or reviewed ≥ 1 PR |
| Issue participation | +5 | created or commented on issues |
| Multiple contributors | +5 | repo has 2+ contributors |

**Red flags:**

| Flag | Points | Condition |
|------|--------|-----------|
| Solo on "group" project | -15 | claimed group but only 1 contributor |
| Coattail riding | -20 | candidate has < 5% of total commits |

#### Layer 4: Structural Red Flags

| Flag | Points | Condition |
|------|--------|-----------|
| Fork of known tutorial | -30 | parent repo in tutorial database |
| Very low contribution | -15 | only 1-2 commits total |
| Only docs/config | -10 | 100% of changes are non-code files |

### Tier 2: AI Deep Analysis (Suspicious Cases Only)

Runs asynchronously in background for submissions scoring < 75.

#### Code Similarity Detection

1. Download repo source files via GitHub API
2. Generate embeddings using OpenAI text-embedding-3-small
3. Compare against tutorial fingerprint database
4. Flag if similarity > 85%

#### LLM Analysis

For edge cases, ask Claude:
- "Does this code structure match common tutorial patterns?"
- "Is this likely AI-generated code?"
- "What's the complexity level of this codebase?"

---

## API Specification

### Endpoints

#### POST /verify-project

Verify a candidate's project contribution.

**Request:**
```json
{
  "candidate_id": "string (required)",
  "candidate_name": "string (required)",
  "github_username": "string (required)",
  "repo_link": "string (required, valid GitHub URL)",
  "project_type": "individual | group (required)"
}
```

**Response (success):**
```json
{
  "candidate_id": "12345",
  "verification_type": "project",
  "verification_id": "ver_abc123",
  "score": 82,
  "max_score": 100,
  "status": "verified | needs_review | suspicious",
  "tier1_complete": true,
  "tier2_complete": false,
  "tier2_status": "pending | completed | not_required",
  "flags": [
    {
      "type": "warning | positive | negative",
      "code": "OWNER_MISMATCH",
      "message": "Repository owner differs from candidate username"
    }
  ],
  "details": {
    "owner": "rahuldev",
    "is_fork": false,
    "candidate_commits": 7,
    "total_commits": 45,
    "candidate_lines_added": 342,
    "file_types_touched": [".py", ".html", ".css"],
    "first_commit_date": "2026-03-15",
    "last_commit_date": "2026-06-20",
    "pr_count": 2,
    "issue_count": 1,
    "contributors_count": 4
  },
  "created_at": "2026-11-03T10:30:00Z"
}
```

**Response (error):**
```json
{
  "error": true,
  "code": "REPO_NOT_FOUND | INVALID_USERNAME | RATE_LIMITED | INTERNAL_ERROR",
  "message": "Repository not found or is private"
}
```

#### GET /verify-project/{verification_id}

Get status of a verification (including Tier 2 results when complete).

**Response:** Same as POST response, with updated tier2_complete and potentially updated score/flags.

#### GET /health

Health check for integration testing.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "github_api": "ok",
  "database": "ok",
  "queue": "ok"
}
```

---

## Scoring

### Score Calculation

```
base_score = sum(positive_checks)
penalties = sum(negative_flags)
final_score = max(0, min(100, base_score + penalties))
```

### Status Thresholds

| Score | Status | Meaning |
|-------|--------|---------|
| ≥ 75 | `verified` | Strong evidence of genuine contribution |
| 45-74 | `needs_review` | Some concerns, manual review recommended |
| < 45 | `suspicious` | High likelihood of fake/minimal contribution |

---

## Database Schema

### Tables

#### verifications

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| candidate_id | VARCHAR | External candidate ID |
| candidate_name | VARCHAR | Candidate name |
| github_username | VARCHAR | GitHub username |
| repo_link | VARCHAR | Repository URL |
| project_type | ENUM | individual / group |
| score | INTEGER | 0-100 |
| status | ENUM | verified / needs_review / suspicious |
| tier1_complete | BOOLEAN | Tier 1 done |
| tier2_complete | BOOLEAN | Tier 2 done |
| flags | JSONB | Array of flag objects |
| details | JSONB | Detailed metrics |
| created_at | TIMESTAMP | When submitted |
| updated_at | TIMESTAMP | Last update |

#### tutorial_fingerprints

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| source_name | VARCHAR | e.g., "freeCodeCamp React Tutorial" |
| source_url | VARCHAR | Original repo URL |
| file_hashes | JSONB | Hash of key files |
| embedding | VECTOR | Code embedding for similarity |
| created_at | TIMESTAMP | When added |

---

## Error Handling

### Principles

1. **Never hang** — all GitHub API calls have timeouts (10s)
2. **Always return JSON** — even on errors
3. **Graceful degradation** — if Tier 2 fails, Tier 1 result still valid
4. **Retry logic** — transient GitHub failures retry 3x with backoff

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| REPO_NOT_FOUND | 404 | Repository doesn't exist or is private |
| INVALID_USERNAME | 400 | GitHub username doesn't exist |
| INVALID_URL | 400 | Not a valid GitHub repository URL |
| RATE_LIMITED | 429 | GitHub API rate limit hit |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Optional
LOG_LEVEL=INFO
TIER2_ENABLED=true
GITHUB_TIMEOUT_SECONDS=10
MAX_RETRIES=3
```

### GitHub Token

Required for:
- 5000 requests/hour (vs 60 unauthenticated)
- Access to contributor statistics
- Reliable rate limiting

---

## Deployment

### Railway/Render Setup

1. **Web Service**: FastAPI app (2 instances for redundancy)
2. **Worker Service**: Celery worker for Tier 2 jobs
3. **PostgreSQL**: Managed database addon
4. **Redis**: Managed Redis addon

### Health Monitoring

- `/health` endpoint checked every 30s
- Auto-restart on crash
- Alerts on sustained errors

---

## Tutorial Fingerprint Database

### Initial Sources (Phase 2)

Curated list of common tutorial/bootcamp repos:

| Category | Examples |
|----------|----------|
| React Tutorials | freeCodeCamp projects, Traversy Media repos |
| Python Bootcamps | 100 Days of Code, Udemy course templates |
| Full-Stack | MERN stack tutorials, Django starter templates |
| ML/AI | Coursera ML course repos, fast.ai templates |

### Maintenance

- Add new tutorials as they're identified
- Community can report common templates
- ~500-1000 repos in initial database

---

## Limitations

### What This System Cannot Detect

1. **Ghostwriting**: Someone else coded under their GitHub account
2. **AI-generated code**: LLM-written code pushed as their own
3. **Private plagiarism**: Copied from private/non-GitHub sources
4. **Paid pair programming**: Partner pushed all commits legitimately

### Why Known Sources Only

Comparing against all of GitHub would:
- Flag common patterns as plagiarism (false positives)
- Be prohibitively slow and expensive
- Not catch the actual fraud (obscure sources)

The curated approach catches 90% of common fraud (tutorial copy-paste) reliably.

---

## Build Phases

### Phase 1: MVP (Week 1)

- FastAPI skeleton with `/verify-project` and `/health`
- GitHub API integration (repo metadata, commits, contributors)
- Tier 1 verification (Layers 1-4)
- PostgreSQL schema and storage
- Basic error handling

**Deliverable:** Working API that returns scores based on GitHub signals

### Phase 2: Plagiarism Detection (Days 3-4)

- Tutorial fingerprint database (50-100 initial repos)
- Hash-based file matching
- Fork detection logic

**Deliverable:** Detects submissions that match known tutorials

### Phase 3: AI Integration (Week 2)

- Redis + Celery setup
- OpenAI embeddings integration
- Code similarity detection
- Claude analysis for edge cases
- Async Tier 2 pipeline

**Deliverable:** Deep analysis for suspicious submissions

### Phase 4: Production Deployment (Days 1-2)

- Railway/Render deployment
- Environment configuration
- Health monitoring
- Integration testing with frontend

**Deliverable:** 24/7 running production system

---

## Success Criteria

1. **Accuracy**: < 5% false positive rate on test dataset
2. **Speed**: Tier 1 response < 5 seconds
3. **Reliability**: 99.5% uptime
4. **Integration**: Frontend can call API without issues

---

## Resolved Decisions

| Decision | Resolution |
|----------|------------|
| Request volume | Assume < 100/day initially, single GitHub token with retry |
| Tier 2 notification | Polling via `GET /verify-project/{id}` |
| Repo size limits | Max 100MB download, shallow clone, sample files if larger |
| Duplicate handling | Deduplicate by repo_link + candidate_id within 24h |
| Tier 2 timeout | 1 hour max, then mark failed, Tier 1 score becomes final |
| Embedding versioning | Store model version in DB, re-embed on model upgrade |
| Verification ID format | UUID with `ver_` prefix |
| Tutorial database | Start with freeCodeCamp, Udemy popular courses, expand later |
