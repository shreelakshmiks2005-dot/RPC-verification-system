from dataclasses import dataclass
from typing import Optional


@dataclass
class FingerprintMatch:
    source_name: str
    source_url: str
    similarity: float
    matched_files: list[str]


class FingerprintMatcher:
    def __init__(self, known_fingerprints: list[dict] = None):
        """
        Initialize with a list of known fingerprints.
        Each fingerprint should have:
        - source_name: str
        - source_url: str (optional)
        - file_hashes: dict[str, str]
        """
        self.fingerprints = known_fingerprints or self._get_default_fingerprints()

    def _get_default_fingerprints(self) -> list[dict]:
        """Return default known tutorial fingerprints."""
        return [
            {
                "source_name": "React Todo Tutorial",
                "source_url": "https://reactjs.org/docs/tutorial",
                "keywords": ["todoitem", "todolist", "addtodo", "removetodo", "toggletodo", "todos"],
                "min_matches": 2,
            },
            {
                "source_name": "Django Polls Tutorial",
                "source_url": "https://docs.djangoproject.com/tutorial",
                "keywords": ["polls", "question", "choice", "vote", "get_queryset"],
                "min_matches": 2,
            },
            {
                "source_name": "Flask Blog Tutorial",
                "source_url": "https://flask.palletsprojects.com/tutorial",
                "keywords": ["flaskr", "create_app", "init_db", "get_db"],
                "min_matches": 2,
            },
            {
                "source_name": "Generic Todo App",
                "source_url": "common-tutorial",
                "keywords": ["todoitem", "todos", "completed", "toggle", "removetodo"],
                "min_matches": 3,
            },
        ]

    async def find_matches(self, code: str) -> list[dict]:
        """Find matches in code against known patterns."""
        matches = []
        code_lower = code.lower()

        for fp in self.fingerprints:
            keywords = fp.get("keywords", [])
            if not keywords:
                continue

            matched_keywords = [kw for kw in keywords if kw in code_lower]
            min_matches = fp.get("min_matches", 2)

            if len(matched_keywords) >= min_matches:
                similarity = len(matched_keywords) / len(keywords)
                matches.append({
                    "source": fp.get("source_name", "Unknown"),
                    "source_url": fp.get("source_url", ""),
                    "similarity": round(similarity, 2),
                    "matched_keywords": matched_keywords,
                })

        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches

    def check_hash_match(
        self, candidate_hashes: dict[str, str], threshold: float = 0.3
    ) -> list[dict]:
        """
        Check if candidate file hashes match any known fingerprints.
        Returns list of matches with similarity scores.
        """
        matches = []

        for fp in self.fingerprints:
            fp_hashes = fp.get("file_hashes", {})
            if not fp_hashes:
                continue

            # Count matching files
            matched_files = []
            for filename, hash_value in candidate_hashes.items():
                if fp_hashes.get(filename) == hash_value:
                    matched_files.append(filename)

            if not matched_files:
                continue

            # Calculate similarity as ratio of matched files to fingerprint files
            similarity = len(matched_files) / len(fp_hashes)

            if similarity >= threshold:
                matches.append({
                    "source_name": fp.get("source_name", "Unknown"),
                    "source_url": fp.get("source_url", ""),
                    "similarity": similarity,
                    "matched_files": matched_files,
                })

        # Sort by similarity descending
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches

    def check_embedding_similarity(
        self,
        candidate_embedding: list[float],
        threshold: float = 0.85,
    ) -> list[dict]:
        """
        Check if candidate embedding is similar to any known fingerprints.
        Uses cosine similarity.
        """
        matches = []

        for fp in self.fingerprints:
            fp_embedding = fp.get("embedding")
            if not fp_embedding:
                continue

            similarity = self._cosine_similarity(candidate_embedding, fp_embedding)

            if similarity >= threshold:
                matches.append({
                    "source_name": fp.get("source_name", "Unknown"),
                    "source_url": fp.get("source_url", ""),
                    "similarity": similarity,
                })

        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
