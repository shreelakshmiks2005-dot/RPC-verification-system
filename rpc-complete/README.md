# Project Verification API

A REST API that verifies whether a candidate genuinely contributed to a GitHub project they claim on their portfolio or resume.

## Features

- **Two-tier verification**: Fast Tier 1 checks using GitHub signals, deep Tier 2 analysis for suspicious cases
- **Multi-layer scoring**: Contribution reality, timing patterns, collaboration depth, red flag detection
- **Plagiarism detection**: Compare code against known tutorial/bootcamp repositories
- **AI-powered analysis**: Code embeddings and LLM analysis for sophisticated fraud detection

## Quick Start

### Local Development

1. **Clone and install dependencies**
```bash
git clone <repo-url>
cd project-verification
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run with Docker Compose**
```bash
docker-compose up
```

Or run locally:
```bash
uvicorn app.main:app --reload
```

### API Endpoints

#### POST /verify-project

Submit a verification request.

```json
{
  "candidate_id": "123",
  "candidate_name": "John Doe",
  "github_username": "johndoe",
  "repo_link": "https://github.com/johndoe/my-project",
  "project_type": "individual"
}
```

Response:
```json
{
  "verification_id": "ver_abc123",
  "score": 82,
  "status": "verified",
  "tier1_complete": true,
  "tier2_complete": false,
  "tier2_status": "not_required",
  "flags": [
    {"type": "positive", "code": "IS_OWNER", "message": "Candidate is the repository owner"}
  ],
  "details": {
    "owner": "johndoe",
    "candidate_commits": 25,
    "contributors_count": 1
  }
}
```

#### GET /verify-project/{verification_id}

Retrieve verification status and results.

#### GET /health

Health check endpoint.

## Scoring System

### Status Thresholds
- **Verified** (≥75): Strong evidence of genuine contribution
- **Needs Review** (45-74): Some concerns, manual review recommended
- **Suspicious** (<45): High likelihood of fake/minimal contribution

### Scoring Factors

**Positive Signals:**
- Repository owner (+30)
- In contributors list (+25)
- 5+ commits (+20)
- Modified code files (+15)
- 100+ lines added (+10)
- Commit spread ≥7 days (+10)
- PR participation (+10)

**Red Flags:**
- All commits in one day (-20)
- Fork of tutorial repo (-10 to -30)
- Coattail riding (<5% of commits) (-20)
- Solo contributor on "group" project (-15)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| REDIS_URL | Redis connection string | Yes |
| GITHUB_TOKEN | GitHub API token | Yes |
| OPENAI_API_KEY | OpenAI API key for embeddings | No |
| ANTHROPIC_API_KEY | Anthropic API key for LLM analysis | No |

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Integration tests only
pytest tests/test_integration.py -v -m integration
```

## Deployment

### Railway / Render

1. Connect your GitHub repository
2. Set environment variables
3. Deploy (auto-detects Procfile)

### Docker

```bash
docker build -t project-verification .
docker run -p 8000:8000 --env-file .env project-verification
```

## Architecture

```
Frontend (external) → FastAPI Backend → GitHub API
                           ↓
                     Tier 1 Scoring
                           ↓
                   Score < 75? → Celery Worker → Tier 2 Analysis
                           ↓
                     PostgreSQL (results)
```

## License

MIT
