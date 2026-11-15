from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime, timezone

from app.services.github_client import GitHubClient
from app.services.scoring import calculate_score, determine_status


@dataclass
class Flag:
    type: Literal["positive", "warning", "negative"]
    code: str
    message: str


@dataclass
class Tier1Result:
    score: int
    status: Literal["verified", "needs_review", "suspicious"]
    flags: list[Flag] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    checks: list[dict] = field(default_factory=list)


# Commit messages that indicate lazy/fake work
JUNK_MESSAGES = {
    "update", "updates", "fix", "fixed", "test", "testing",
    "commit", "done", "work", "change", "changes", "changed",
    ".", "..", "...", "initial", "first commit", "init",
    "wip", "temp", "tmp", "asdf", "aaa", "abc", "hello",
    "add files", "add file", "new file", "added", "upload",
    "uploaded files", "uploading", "uploaded"
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".rb", ".php", ".swift", ".kt", ".cs",
    ".html", ".css", ".scss", ".vue", ".dart", ".r", ".m",
}


class Tier1Verifier:
    def __init__(self, github_client: GitHubClient):
        self.client = github_client

    # ──────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────

    def _matches_user(self, commit, username_lower: str) -> bool:
        """Fuzzy match commit author against GitHub username."""
        if not commit.author:
            return False
        a = commit.author.lower()
        if a == username_lower:
            return True
        if username_lower in a or a in username_lower:
            return True
        # strip dots/dashes: "shreelakshmiks2005-dot" → "shreelakshmiks2005dot"
        clean_u = username_lower.replace("-", "").replace("_", "").replace(".", "")
        clean_a = a.replace("-", "").replace("_", "").replace(".", "")
        if clean_u[:8] in clean_a or clean_a[:8] in clean_u:
            return True
        return False

    def _parse_dt(self, date_str: str):
        """Parse ISO date string to timezone-aware datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _score_message_quality(self, messages: list[str]) -> tuple[int, int]:
        """Return (quality_count, junk_count) for a list of commit messages."""
        quality = 0
        junk = 0
        for msg in messages:
            clean = msg.strip().lower().split("\n")[0]  # first line only
            if clean in JUNK_MESSAGES or len(clean) < 5:
                junk += 1
            elif len(clean) >= 15:
                quality += 1
        return quality, junk

    # ──────────────────────────────────────────────────────────
    # MAIN VERIFY
    # ──────────────────────────────────────────────────────────

    async def verify(
        self,
        github_username: str,
        repo_url: str,
        project_type: Literal["individual", "group"],
    ) -> Tier1Result:

        owner, repo_name = self.client.parse_repo_url(repo_url)
        username_lower = github_username.lower()

        # ── Fetch core data ──────────────────────────────────
        repo_data     = await self.client.get_repo(owner, repo_name)
        contributors  = await self.client.get_contributors(owner, repo_name)
        all_commits   = await self.client.get_commits(owner, repo_name)
        user_prs      = await self.client.get_pull_requests(owner, repo_name, author=github_username)

        # ── Fetch user profile (account age + completeness) ──
        try:
            profile = await self.client.get_user_profile(github_username)
        except Exception:
            profile = None

        # ── Filter user commits (fuzzy match) ────────────────
        is_owner = repo_data.owner.lower() == username_lower
        user_commits = [c for c in all_commits if self._matches_user(c, username_lower)]

        # Solo owner with unlinked git email → attribute all commits
        if is_owner and not user_commits and len(contributors) <= 1:
            user_commits = all_commits

        # ── Fetch commit file stats for top 10 user commits ──
        # This gives real additions/deletions and file names
        commit_stats = []
        for c in user_commits[:10]:
            stat = await self.client.get_commit_detail(owner, repo_name, c.sha)
            commit_stats.append(stat)

        checks = []
        flags  = []

        # ════════════════════════════════════════════════════
        # LAYER 0: ACCOUNT VERIFICATION (new)
        # ════════════════════════════════════════════════════
        if profile:
            account_created = self._parse_dt(profile.get("created_at", ""))
            repo_created    = self._parse_dt(repo_data.created_at)
            now             = datetime.now(timezone.utc)

            if account_created:
                account_age_days = (now - account_created).days

                # Account created AFTER the repo — impossible unless repo was transferred
                if repo_created and account_created > repo_created:
                    checks.append({"name": "account_older_than_repo", "points": -20, "passed": True})
                    flags.append(Flag("negative", "ACCOUNT_NEWER_THAN_REPO",
                        f"GitHub account created after the repository — possible ownership transfer or fake"))

                # Very new account (< 30 days) submitting a project
                elif account_age_days < 30:
                    checks.append({"name": "account_age", "points": -15, "passed": True})
                    flags.append(Flag("negative", "NEW_ACCOUNT",
                        f"GitHub account is only {account_age_days} days old — may be throwaway account"))

                # Young account (30–180 days)
                elif account_age_days < 180:
                    checks.append({"name": "account_age", "points": 0, "passed": False})
                    flags.append(Flag("warning", "YOUNG_ACCOUNT",
                        f"GitHub account is {account_age_days} days old — relatively new"))

                # Established account (> 6 months)
                else:
                    checks.append({"name": "account_age", "points": 5, "passed": True})
                    flags.append(Flag("positive", "ESTABLISHED_ACCOUNT",
                        f"GitHub account is {account_age_days // 30} months old"))

            # Profile completeness score
            completeness = 0
            if profile.get("name"):         completeness += 1
            if profile.get("bio"):          completeness += 1
            if profile.get("has_avatar"):   completeness += 1
            if profile.get("blog"):         completeness += 1
            if profile.get("public_repos", 0) > 1: completeness += 1
            if profile.get("followers", 0)  > 0:   completeness += 1

            if completeness >= 4:
                checks.append({"name": "profile_complete", "points": 5, "passed": True})
                flags.append(Flag("positive", "COMPLETE_PROFILE",
                    f"Well-established GitHub profile (repos={profile.get('public_repos')}, "
                    f"followers={profile.get('followers')})"))
            elif completeness <= 1:
                checks.append({"name": "profile_complete", "points": -5, "passed": True})
                flags.append(Flag("warning", "EMPTY_PROFILE",
                    "Minimal GitHub profile — no bio, avatar, or activity"))

        # ════════════════════════════════════════════════════
        # LAYER 1: CONTRIBUTION REALITY
        # ════════════════════════════════════════════════════

        checks.append({"name": "is_owner", "points": 30, "passed": is_owner})
        if is_owner:
            flags.append(Flag("positive", "IS_OWNER", "Candidate is the repository owner"))

        is_contributor = any(
            c.login.lower() == username_lower or
            username_lower in c.login.lower() or
            c.login.lower() in username_lower
            for c in contributors
        )
        checks.append({"name": "is_contributor", "points": 25, "passed": is_contributor})
        if is_contributor:
            flags.append(Flag("positive", "IS_CONTRIBUTOR", "Candidate is in the contributors list"))

        commit_count = len(user_commits)
        has_enough_commits = commit_count >= 5
        checks.append({"name": "commit_count", "points": 20, "passed": has_enough_commits})
        if has_enough_commits:
            flags.append(Flag("positive", "ENOUGH_COMMITS", f"Candidate has {commit_count} commits"))

        # Real file stats from commit details
        total_additions  = sum(s.get("additions", 0) for s in commit_stats)
        total_deletions  = sum(s.get("deletions", 0) for s in commit_stats)
        all_files_touched = set()
        for s in commit_stats:
            all_files_touched.update(s.get("files", []))

        code_files_touched = any(
            any(f.endswith(ext) for ext in CODE_EXTENSIONS)
            for f in all_files_touched
        )
        checks.append({"name": "code_files_touched", "points": 15, "passed": code_files_touched})
        if code_files_touched:
            code_files = [f for f in all_files_touched
                          if any(f.endswith(ext) for ext in CODE_EXTENSIONS)]
            flags.append(Flag("positive", "TOUCHED_CODE",
                f"Candidate modified {len(code_files)} code file(s): "
                f"{', '.join(list(code_files)[:3])}{'...' if len(code_files) > 3 else ''}"))

        enough_lines = total_additions >= 100
        checks.append({"name": "lines_of_code", "points": 10, "passed": enough_lines})
        if enough_lines:
            flags.append(Flag("positive", "ENOUGH_LINES",
                f"Candidate added {total_additions} lines of code"))

        # ── File diversity check (new) ──────────────────────
        readme_only = (
            len(all_files_touched) > 0 and
            all(f.lower() in ("readme.md", "readme.txt", "readme", ".gitignore", "license")
                for f in all_files_touched)
        )
        if readme_only:
            checks.append({"name": "file_diversity", "points": -15, "passed": True})
            flags.append(Flag("negative", "README_ONLY_COMMITS",
                "All candidate commits only modified README/config files — no actual code contribution"))
        elif len(all_files_touched) >= 3:
            checks.append({"name": "file_diversity", "points": 5, "passed": True})
            flags.append(Flag("positive", "DIVERSE_FILES",
                f"Candidate touched {len(all_files_touched)} different files"))

        # ════════════════════════════════════════════════════
        # LAYER 2: TIMING PATTERNS + BACKDATING (new)
        # ════════════════════════════════════════════════════

        backdated_count = 0
        for s in commit_stats:
            author_dt    = self._parse_dt(s.get("author_date", ""))
            committer_dt = self._parse_dt(s.get("committer_date", ""))
            if author_dt and committer_dt:
                diff_days = abs((committer_dt - author_dt).days)
                if diff_days > 7:   # commit date is > 7 days before push date
                    backdated_count += 1

        if backdated_count > 0:
            pct_backdated = round(backdated_count / max(len(commit_stats), 1) * 100)
            checks.append({"name": "backdated_commits", "points": -15, "passed": True})
            flags.append(Flag("negative", "BACKDATED_COMMITS",
                f"{backdated_count} commit(s) ({pct_backdated}%) have backdated timestamps "
                f"— git date set manually"))

        if user_commits:
            dates = [self._parse_dt(c.date) for c in user_commits if c.date]
            dates = [d for d in dates if d]

            if len(dates) >= 2:
                dates.sort()
                span = (dates[-1] - dates[0]).days

                commit_spread = span >= 7
                checks.append({"name": "commit_spread", "points": 10, "passed": commit_spread})
                if commit_spread:
                    flags.append(Flag("positive", "COMMIT_SPREAD",
                        f"Commits span {span} days — consistent development"))

                # Burst detection
                one_day_max = max(
                    sum(1 for d2 in dates if abs((d2 - d).total_seconds()) < 86400)
                    for d in dates
                )
                burst_ratio = one_day_max / len(dates)
                no_burst = burst_ratio < 0.8
                checks.append({"name": "no_burst", "points": 5, "passed": no_burst})

                all_same_day = span == 0 and len(dates) > 1
                checks.append({"name": "all_commits_one_day", "points": -20, "passed": all_same_day})
                if all_same_day:
                    flags.append(Flag("negative", "ALL_COMMITS_ONE_DAY",
                        "All commits made in a single day — bulk upload suspected"))

            if dates:
                last_commit = max(dates)
                now_tz = datetime.now(last_commit.tzinfo)
                months_ago = (now_tz - last_commit).days / 30

                recent = months_ago <= 6
                checks.append({"name": "recent_activity", "points": 5, "passed": recent})
                if recent:
                    flags.append(Flag("positive", "RECENT_ACTIVITY",
                        f"Last commit was {int(months_ago * 30)} days ago"))

                ancient = months_ago > 24
                checks.append({"name": "ancient_untouched", "points": -10, "passed": ancient})
                if ancient:
                    flags.append(Flag("negative", "ANCIENT",
                        f"No commits in over {int(months_ago / 12)} year(s)"))

        # ════════════════════════════════════════════════════
        # LAYER 2b: COMMIT MESSAGE QUALITY (new)
        # ════════════════════════════════════════════════════

        if user_commits:
            messages = [c.message for c in user_commits if c.message]
            quality_count, junk_count = self._score_message_quality(messages)
            total_msgs = len(messages)

            junk_ratio = junk_count / total_msgs if total_msgs else 0

            if junk_ratio >= 0.6:
                checks.append({"name": "commit_quality", "points": -10, "passed": True})
                flags.append(Flag("negative", "POOR_COMMIT_MESSAGES",
                    f"{junk_count}/{total_msgs} commits have junk messages like 'update', 'fix', '.' "
                    f"— indicates low-effort or fake contribution"))
            elif quality_count >= 3:
                checks.append({"name": "commit_quality", "points": 5, "passed": True})
                flags.append(Flag("positive", "GOOD_COMMIT_MESSAGES",
                    f"{quality_count} descriptive commit messages — indicates genuine development work"))

        # ════════════════════════════════════════════════════
        # LAYER 3: COLLABORATION (group projects)
        # ════════════════════════════════════════════════════

        if project_type == "group":
            has_prs = len(user_prs) >= 1
            checks.append({"name": "pr_participation", "points": 10, "passed": has_prs})
            if has_prs:
                flags.append(Flag("positive", "HAS_PRS",
                    f"Candidate has {len(user_prs)} pull request(s)"))

            multiple_contributors = len(contributors) >= 2
            checks.append({"name": "multiple_contributors", "points": 5, "passed": multiple_contributors})
            if multiple_contributors:
                flags.append(Flag("positive", "MULTI_CONTRIBUTOR",
                    f"Repository has {len(contributors)} contributors — genuine group project"))

            solo_group = len(contributors) <= 1
            checks.append({"name": "solo_group_project", "points": -15, "passed": solo_group})
            if solo_group:
                flags.append(Flag("negative", "SOLO_GROUP",
                    "Claimed group project has only 1 contributor — may be individual work"))

            # Contribution balance (new: works for small teams too)
            if all_commits and len(contributors) >= 2:
                contribution_ratio = len(user_commits) / len(all_commits) if all_commits else 0
                coattail_threshold = 0.05 if len(contributors) > 5 else 0.10
                coattail = contribution_ratio < coattail_threshold
                checks.append({"name": "coattail_riding", "points": -20, "passed": coattail})
                if coattail:
                    pct = round(contribution_ratio * 100, 1)
                    flags.append(Flag("negative", "COATTAIL",
                        f"Candidate has only {pct}% of total commits — possible coattail riding"))
                else:
                    pct = round(contribution_ratio * 100, 1)
                    if pct >= 30:
                        flags.append(Flag("positive", "ACTIVE_CONTRIBUTOR",
                            f"Candidate made {pct}% of team commits — active contributor"))

            # Contribution balance across all members (new)
            if contributors and len(contributors) >= 2:
                total_contribs = sum(c.contributions for c in contributors)
                if total_contribs > 0:
                    candidate_contribs = next(
                        (c.contributions for c in contributors
                         if self._matches_user(
                             type('Commit', (), {'author': c.login})(), username_lower)),
                        0
                    )
                    candidate_share = candidate_contribs / total_contribs
                    expected_share  = 1 / len(contributors)

                    if candidate_share < expected_share * 0.3 and candidate_share < 0.05:
                        flags.append(Flag("negative", "IMBALANCED_CONTRIBUTION",
                            f"Candidate contributed {round(candidate_share*100, 1)}% — "
                            f"expected ~{round(expected_share*100)}% for a {len(contributors)}-person team"))

            if commit_count == 0 and len(all_commits) > 0:
                checks.append({"name": "no_group_commits", "points": -25, "passed": True})
                flags.append(Flag("negative", "NO_GROUP_COMMITS",
                    "Candidate has 0 commits in this group project"))

        if project_type == "individual":
            if not is_owner and len(contributors) > 3:
                flags.append(Flag("warning", "NOT_OWNER_LARGE_REPO",
                    f"Candidate is not the owner of a {len(contributors)}-contributor repo"))

        # ════════════════════════════════════════════════════
        # LAYER 4: RED FLAGS
        # ════════════════════════════════════════════════════

        is_fork = repo_data.is_fork
        checks.append({"name": "is_fork", "points": -10 if is_fork else 10, "passed": not is_fork})
        if is_fork:
            flags.append(Flag("negative", "IS_FORK",
                f"Repository is a fork of {repo_data.parent_url or 'another repo'}"))

        very_low = commit_count <= 2 and not is_owner
        checks.append({"name": "very_low_contribution", "points": -15, "passed": very_low})
        if very_low and commit_count > 0:
            flags.append(Flag("negative", "LOW_CONTRIBUTION",
                f"Only {commit_count} commit(s) — very low contribution"))

        # ── Score ────────────────────────────────────────────
        score  = calculate_score(checks)
        status = determine_status(score)

        details = {
            "owner":                repo_data.owner,
            "is_fork":              repo_data.is_fork,
            "candidate_commits":    commit_count,
            "total_commits":        len(all_commits),
            "candidate_lines_added": total_additions,
            "candidate_lines_deleted": total_deletions,
            "files_touched":        len(all_files_touched),
            "code_files_touched":   [f for f in list(all_files_touched)[:10]
                                     if any(f.endswith(e) for e in CODE_EXTENSIONS)],
            "contributors_count":   len(contributors),
            "pr_count":             len(user_prs),
            "backdated_commits":    backdated_count,
            "account_age_days":     (
                (datetime.now(timezone.utc) -
                 self._parse_dt(profile.get("created_at", ""))).days
                if profile and profile.get("created_at") else None
            ),
            "public_repos":         profile.get("public_repos") if profile else None,
            "followers":            profile.get("followers") if profile else None,
        }

        return Tier1Result(
            score=score,
            status=status,
            flags=flags,
            details=details,
            checks=checks,
        )
