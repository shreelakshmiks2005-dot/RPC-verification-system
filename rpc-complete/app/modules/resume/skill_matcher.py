"""
Skill Matching Module
Matches extracted skills against job requirements
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillMatch:
    skill: str
    category: str
    confidence: float  # 0.0 to 1.0
    found_in_resume: bool
    required: bool = False


@dataclass
class SkillMatchResult:
    total_skills_found: int
    required_skills_matched: int
    required_skills_total: int
    match_percentage: float
    skill_matches: list[SkillMatch] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    additional_skills: list[str] = field(default_factory=list)


class SkillMatcher:
    """Matches resume skills against job requirements."""

    # Skill categories
    SKILL_CATEGORIES = {
        "programming": [
            "python", "java", "javascript", "typescript", "c++", "c#", "go",
            "rust", "ruby", "php", "swift", "kotlin", "scala", "r"
        ],
        "frontend": [
            "react", "angular", "vue", "svelte", "html", "css", "sass",
            "tailwind", "bootstrap", "jquery", "webpack", "next.js", "nuxt"
        ],
        "backend": [
            "node.js", "express", "django", "flask", "fastapi", "spring",
            "rails", "laravel", "asp.net", "gin", "fiber"
        ],
        "database": [
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "cassandra", "dynamodb", "sqlite", "oracle", "neo4j"
        ],
        "cloud": [
            "aws", "azure", "gcp", "heroku", "digitalocean", "cloudflare",
            "firebase", "vercel", "netlify"
        ],
        "devops": [
            "docker", "kubernetes", "terraform", "ansible", "jenkins",
            "github actions", "gitlab ci", "circleci", "prometheus", "grafana"
        ],
        "ml_ai": [
            "machine learning", "deep learning", "tensorflow", "pytorch",
            "keras", "scikit-learn", "numpy", "pandas", "opencv", "nlp"
        ],
        "tools": [
            "git", "linux", "bash", "vim", "vscode", "jira", "confluence",
            "slack", "figma", "postman"
        ],
    }

    # Skill synonyms/aliases
    SKILL_ALIASES = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "node": "node.js",
        "postgres": "postgresql",
        "mongo": "mongodb",
        "k8s": "kubernetes",
        "tf": "terraform",
        "ml": "machine learning",
        "dl": "deep learning",
        "ai": "machine learning",
    }

    def __init__(self):
        # Build reverse lookup for categories
        self._skill_to_category = {}
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                self._skill_to_category[skill] = category

    def match(
        self,
        resume_skills: list[str],
        required_skills: list[str] = None,
        preferred_skills: list[str] = None,
    ) -> SkillMatchResult:
        """
        Match resume skills against requirements.

        Args:
            resume_skills: Skills extracted from resume
            required_skills: Must-have skills for the job
            preferred_skills: Nice-to-have skills

        Returns:
            SkillMatchResult with match analysis
        """
        required_skills = required_skills or []
        preferred_skills = preferred_skills or []

        # Normalize skills
        resume_normalized = self._normalize_skills(resume_skills)
        required_normalized = self._normalize_skills(required_skills)
        preferred_normalized = self._normalize_skills(preferred_skills)

        skill_matches = []
        missing_required = []
        additional_skills = []

        # Check required skills
        required_matched = 0
        for skill in required_normalized:
            found = skill in resume_normalized
            if found:
                required_matched += 1
            else:
                missing_required.append(skill)

            skill_matches.append(SkillMatch(
                skill=skill,
                category=self._skill_to_category.get(skill, "other"),
                confidence=1.0 if found else 0.0,
                found_in_resume=found,
                required=True,
            ))

        # Check preferred skills
        for skill in preferred_normalized:
            if skill in required_normalized:
                continue  # Already counted
            found = skill in resume_normalized
            skill_matches.append(SkillMatch(
                skill=skill,
                category=self._skill_to_category.get(skill, "other"),
                confidence=1.0 if found else 0.0,
                found_in_resume=found,
                required=False,
            ))

        # Find additional skills in resume
        all_required_preferred = set(required_normalized) | set(preferred_normalized)
        for skill in resume_normalized:
            if skill not in all_required_preferred:
                additional_skills.append(skill)
                skill_matches.append(SkillMatch(
                    skill=skill,
                    category=self._skill_to_category.get(skill, "other"),
                    confidence=1.0,
                    found_in_resume=True,
                    required=False,
                ))

        # Calculate match percentage
        if required_normalized:
            match_percentage = (required_matched / len(required_normalized)) * 100
        else:
            match_percentage = 100.0 if resume_normalized else 0.0

        return SkillMatchResult(
            total_skills_found=len(resume_normalized),
            required_skills_matched=required_matched,
            required_skills_total=len(required_normalized),
            match_percentage=round(match_percentage, 2),
            skill_matches=skill_matches,
            missing_required=missing_required,
            additional_skills=additional_skills,
        )

    def _normalize_skills(self, skills: list[str]) -> set[str]:
        """Normalize skill names using aliases."""
        normalized = set()
        for skill in skills:
            skill_lower = skill.lower().strip()
            # Check aliases
            if skill_lower in self.SKILL_ALIASES:
                skill_lower = self.SKILL_ALIASES[skill_lower]
            normalized.add(skill_lower)
        return normalized

    def get_skill_category(self, skill: str) -> str:
        """Get the category for a skill."""
        skill_lower = skill.lower().strip()
        if skill_lower in self.SKILL_ALIASES:
            skill_lower = self.SKILL_ALIASES[skill_lower]
        return self._skill_to_category.get(skill_lower, "other")

    def categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """Group skills by category."""
        categorized = {}
        for skill in skills:
            category = self.get_skill_category(skill)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(skill)
        return categorized
