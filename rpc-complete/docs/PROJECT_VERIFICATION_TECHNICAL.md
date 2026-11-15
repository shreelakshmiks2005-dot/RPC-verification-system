# Project Verification Module — Complete Technical Documentation

**System:** RPC Verification System  
**Module:** Project Validation (GitHub API — 2-Tier Analysis)  
**Weight in Trust Score:** w₂ = 0.50 (50%)  

---

## Overview

The Project Validation module determines whether a candidate genuinely contributed to the GitHub repository they claim on their resume. It uses the **GitHub REST API** exclusively — no code download required.

The module runs in two tiers:
- **Tier 1** — Fast analysis using GitHub signals (~3–5 seconds)
- **Tier 2** — Deep plagiarism detection, runs only when Tier 1 score < 75 (~5–10 seconds extra)

---

## Step-by-Step: How a Project Gets Verified

### Step 1 — URL Parsing

```
Input:  https://github.com/shreelakshmiks2005-dot/RPC-verification-system
         ↓
Parse:  owner = "shreelakshmiks2005-dot"
        repo  = "RPC-verification-system"
```

Handled automatically:
- `.git` suffix stripped (`repo.git` → `repo`)
- Trailing slashes stripped
- `www.github.com` accepted

---

### Step 2 — GitHub API Calls (Tier 1)

6 API calls run in sequence:

```
1. GET /repos/{owner}/{repo}
   → is_fork, stars, created_at, parent_url

2. GET /repos/{owner}/{repo}/contributors
   → list of contributors with commit counts

3. GET /repos/{owner}/{repo}/commits?per_page=100
   → up to 100 most recent commits with author info

4. GET /repos/{owner}/{repo}/commits/{sha}  (top 10 user commits)
   → real file stats: additions, deletions, filenames
   → author_date vs committer_date (for backdating detection)

5. GET /repos/{owner}/{repo}/pulls?state=all
   → pull requests (for group project collaboration check)

6. GET /users/{github_username}
   → account age, public repos, followers, bio, avatar
```

**Username Fuzzy Matching:**  
When git emails aren't linked to GitHub accounts, `author` field on commits is `null`. The system falls back to matching by git author name using fuzzy logic:

```python
# "shreelakshmiks2005" matches "shreelakshmiks2005-dot"
# Strip dots, dashes, underscores and compare first 8 chars
clean_u = username.replace("-","").replace("_","").replace(".","")
clean_a = author.replace("-","").replace("_","").replace(".","")
if clean_u[:8] in clean_a → MATCH
```

---

### Step 3 — Tier 1 Scoring (12 Layers)

Base score starts at 0. Points are added/subtracted based on signals.

#### Layer 0: Account Verification (NEW)

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Established account | Age > 180 days | +5 | `ESTABLISHED_ACCOUNT` |
| Young account | Age 30–180 days | 0 | `YOUNG_ACCOUNT` (warning) |
| New account | Age < 30 days | −15 | `NEW_ACCOUNT` |
| Account newer than repo | Created after repo | −20 | `ACCOUNT_NEWER_THAN_REPO` |
| Complete profile | Bio + avatar + repos + followers | +5 | `COMPLETE_PROFILE` |
| Empty profile | No bio, no avatar | −5 | `EMPTY_PROFILE` (warning) |

#### Layer 1: Contribution Reality

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Repository owner | `repo.owner == username` | +30 | `IS_OWNER` |
| In contributors list | Username in contributor list | +25 | `IS_CONTRIBUTOR` |
| Enough commits | ≥ 5 commits | +20 | `ENOUGH_COMMITS` |
| Touched code files | Modified `.py/.js/.ts/.java` etc. | +15 | `TOUCHED_CODE` |
| Enough lines added | ≥ 100 lines added | +10 | `ENOUGH_LINES` |
| File diversity | Touched ≥ 3 different files | +5 | `DIVERSE_FILES` |
| README only | All commits only touched README/.gitignore | −15 | `README_ONLY_COMMITS` |

#### Layer 2: Timing Patterns

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Commit spread | Commits span ≥ 7 days | +10 | `COMMIT_SPREAD` |
| No burst | < 80% commits in one day | +5 | — |
| All commits one day | All commits on same date | −20 | `ALL_COMMITS_ONE_DAY` |
| Recent activity | Last commit ≤ 6 months ago | +5 | `RECENT_ACTIVITY` |
| Ancient repo | No commits in 2+ years | −10 | `ANCIENT` |

#### Layer 2b: Backdating Detection (NEW)

Compares `commit.author.date` (what git recorded) vs `commit.committer.date` (when actually pushed to GitHub). These are stored separately by GitHub API.

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Backdated commits | Author date > 7 days before committer date | −15 | `BACKDATED_COMMITS` |

**Example:**
```
git commit --date="2024-01-01" -m "fake old commit"
(actually pushed on 2026-11-10)

author_date    = 2024-01-01   ← what candidate set
committer_date = 2026-11-10   ← when actually pushed
difference     = 679 days → BACKDATED_COMMITS flag
```

#### Layer 2c: Commit Message Quality (NEW)

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Good messages | ≥ 3 descriptive messages (≥15 chars) | +5 | `GOOD_COMMIT_MESSAGES` |
| Poor messages | ≥ 60% junk messages | −10 | `POOR_COMMIT_MESSAGES` |

**Junk messages detected:** `"update"`, `"fix"`, `"done"`, `"test"`, `"commit"`, `"."`, `"added"`, `"upload"`, `"wip"`, `"init"`, etc.

#### Layer 3: Collaboration (Group Projects Only)

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Has pull requests | ≥ 1 PR by candidate | +10 | `HAS_PRS` |
| Multiple contributors | ≥ 2 contributors | +5 | `MULTI_CONTRIBUTOR` |
| Solo group project | Only 1 contributor total | −15 | `SOLO_GROUP` |
| Coattail riding | Candidate < 10% of commits | −20 | `COATTAIL` |
| Active contributor | Candidate ≥ 30% of commits | — | `ACTIVE_CONTRIBUTOR` |
| Zero commits | Candidate has 0 commits | −25 | `NO_GROUP_COMMITS` |

#### Layer 4: Red Flags

| Signal | Condition | Points | Flag |
|--------|-----------|--------|------|
| Not a fork | repo.is_fork == False | +10 | — |
| Is a fork | repo.is_fork == True | −10 | `IS_FORK` |
| Very low contribution | ≤ 2 commits AND not owner | −15 | `LOW_CONTRIBUTION` |

---

### Step 4 — Tier 2 Decision

```
if Tier1Score >= 75:
    tier2_status = "not_required"
    final_score  = tier1_score
    (stop here)

if Tier1Score < 75:
    run Tier 2 deep analysis
    final_score = clamp(tier1_score + tier2_adjustment, 0, 100)
```

---

### Step 5 — Tier 2 Deep Analysis (Plagiarism Detection)

Runs 4 additional GitHub API checks when Tier 1 score < 75:

#### Check 1: Fork of Popular Repo
```
If repo.is_fork == True:
    fetch parent repo
    if parent.stars > 1000:
        → FORK_OF_POPULAR flag (−15)
        → plagiarism_detected = True
```

#### Check 2: Commit Pattern Analysis
```
Fetch up to 100 commits
If ≥ 5 commits all on same day:
    → SINGLE_DAY_COMMITS flag (−15)

If > 50% of commit intervals < 60 seconds:
    → BURST_COMMITS flag (−10)  ← script-generated commits
```

#### Check 3: Bulk Upload Detection
```
Fetch first (oldest) commit stats:
If additions > 5000 AND files_changed > 20:
    → BULK_INITIAL_COMMIT flag (−20)
    → plagiarism_detected = True

If total_commits ≤ 3 AND total_lines > 2000:
    → FEW_COMMITS_LARGE_PROJECT flag (−10)
```

#### Check 4: Tutorial/Bootcamp Detection
```
Check repo name and description for keywords:
"tutorial", "bootcamp", "homework", "assignment",
"practice", "learning", "course", "exercise"

If matched:
    → TUTORIAL_INDICATORS flag (−5)

If fork chain detected (fork of a fork):
    → FORK_OF_FORK flag (−10)
```

---

### Step 6 — Cross-Module Validation (Full Verification Only)

When Full Verification is run (Resume + Project together):

```
Resume extracted GitHub link: "https://github.com/shreelakshmiks2005"
Submitted GitHub username:    "shreelakshmiks2005-dot"

Fuzzy match: strip dashes → "shreelakshmiks2005" matches "shreelakshmiks2005dot"
Result: GITHUB_RESUME_MATCH → identity confirmed ✓
```

| Scenario | Flag | Penalty |
|----------|------|---------|
| Resume link matches username (individual) | `GITHUB_RESUME_MATCH` | +0 (positive) |
| Resume link ≠ username (individual) | `GITHUB_RESUME_MISMATCH` | −15 |
| Resume link ≠ username (group, expected) | `GITHUB_RESUME_DIFFERENT_MEMBER` | +0 (warning only) |

---

## Live Test Results

### Test 1: Genuine Owner — RPC Verification System

```
Candidate:  Shreelakshmi K S
Username:   shreelakshmiks2005-dot
Repo:       RPC-verification-system
Type:       Individual

Tier 1 Score: 100/100 ✅ VERIFIED
Tier 2:       Not required

Flags:
  ✓ ESTABLISHED_ACCOUNT   — 14 month old GitHub account
  ✓ IS_OWNER              — Candidate owns the repository
  ✓ ENOUGH_COMMITS        — 8 commits
  ✓ TOUCHED_CODE          — 311 code files modified
  ✓ ENOUGH_LINES          — 273,199 lines added
  ✓ DIVERSE_FILES         — 334 different files touched
  ✓ COMMIT_SPREAD         — Commits span 61 days
  ✓ RECENT_ACTIVITY       — Last commit 57 days ago
  ✓ GOOD_COMMIT_MESSAGES  — 7 descriptive commit messages

Details:
  Candidate commits: 8 / 8 total
  Lines added:       273,199
  Backdated:         0 commits
  Account age:       424 days
```

---

### Test 2: Bulk Upload Fraud — cipherSeek

```
Candidate:  Amulya P
Username:   Amulya876
Repo:       cipherSeek
Type:       Individual

Tier 1 Score: 55/100
Tier 2 Score: 55 + (−30) = 25/100 ❌ SUSPICIOUS

Tier 1 Flags:
  ✓ ESTABLISHED_ACCOUNT   — 43 month old account
  ⚠ EMPTY_PROFILE         — No bio, no avatar
  ✓ IS_OWNER              — Owns the repo
  ✓ TOUCHED_CODE          — 139 code files
  ✓ ENOUGH_LINES          — 797,642 lines
  ✗ ALL_COMMITS_ONE_DAY   — All 3 commits on same day

Tier 2 Flags:
  ✗ BULK_INITIAL_COMMIT          — First commit: 797,642 lines, 300 files
  ✗ FEW_COMMITS_LARGE_PROJECT    — Only 3 commits for 797K+ lines

Conclusion: Downloaded existing project as ZIP,
            extracted, and uploaded in one shot.
```

---

### Test 3: Same Repo — Individual vs Group

```
Repo: RPC-verification-system (1 contributor only)

As INDIVIDUAL: Score = 100 ✅ VERIFIED
  (Solo ownership is correct for individual project)

As GROUP:      Score = 65  ⚠ NEEDS REVIEW
  Added flag: ✗ SOLO_GROUP — Only 1 contributor on claimed group project
  Deducted: −15 points
```

---

## Score Thresholds

| Score | Status | Recruiter Action |
|-------|--------|-----------------|
| ≥ 75 | **Verified** ✅ | Approve candidate |
| 45–74 | **Needs Review** ⚠ | Manual review |
| < 45 | **Suspicious** ❌ | Reject / investigate |

---

## What the System Cannot Detect (Limitations)

| Fraud Type | Reason |
|------------|--------|
| Code copied but committed gradually over weeks | Looks like genuine work by timing signals |
| Paid developer wrote and committed the code | No way to verify authorship from GitHub signals alone |
| AI-generated code committed properly | Indistinguishable from human commits via GitHub API |
| Copied from a private or deleted repository | No reference to compare against |

These would require **code content analysis** or **LLM authorship fingerprinting** — planned as future scope (Section 5.2 of project report).

---

## Files Involved

| File | Purpose |
|------|---------|
| `app/services/github_client.py` | All GitHub API calls, URL parsing, user profile, commit stats |
| `app/services/tier1_verifier.py` | All Tier 1 scoring layers (0–4) |
| `app/services/tier2_verifier.py` | Deep plagiarism detection (Tier 2) |
| `app/services/scoring.py` | `calculate_score()` and `determine_status()` helpers |
| `app/api/routes.py` | API endpoint, Tier 1 + Tier 2 orchestration, cross-module check |

---

*RPC Verification System — SIT Tumakuru, Dept. of CSE, 2025–26*
