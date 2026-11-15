import uuid


def test_fingerprint_model_has_required_fields():
    from app.models.fingerprint import TutorialFingerprint

    fp = TutorialFingerprint(
        id=uuid.uuid4(),
        source_name="freeCodeCamp React Tutorial",
        source_url="https://github.com/freeCodeCamp/freeCodeCamp",
        file_hashes={"main.js": "abc123", "App.js": "def456"},
    )
    assert fp.source_name == "freeCodeCamp React Tutorial"
    assert "main.js" in fp.file_hashes


def test_fingerprint_matcher_detects_hash_match():
    from app.services.fingerprint_matcher import FingerprintMatcher

    # Create a matcher with some known fingerprints
    known_fingerprints = [
        {
            "source_name": "React Todo Tutorial",
            "file_hashes": {"App.js": "abc123", "index.js": "def456"},
        },
        {
            "source_name": "Flask API Tutorial",
            "file_hashes": {"app.py": "ghi789", "routes.py": "jkl012"},
        },
    ]

    matcher = FingerprintMatcher(known_fingerprints)

    # Test with matching hashes
    candidate_hashes = {"App.js": "abc123", "index.js": "def456", "styles.css": "xyz999"}
    matches = matcher.check_hash_match(candidate_hashes)

    assert len(matches) == 1
    assert matches[0]["source_name"] == "React Todo Tutorial"
    assert matches[0]["similarity"] > 0.5


def test_fingerprint_matcher_no_match():
    from app.services.fingerprint_matcher import FingerprintMatcher

    known_fingerprints = [
        {
            "source_name": "React Todo Tutorial",
            "file_hashes": {"App.js": "abc123"},
        },
    ]

    matcher = FingerprintMatcher(known_fingerprints)

    # Test with non-matching hashes
    candidate_hashes = {"main.py": "different123"}
    matches = matcher.check_hash_match(candidate_hashes)

    assert len(matches) == 0
