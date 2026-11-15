def test_calculate_score_sums_positive_checks():
    from app.services.scoring import calculate_score

    checks = [
        {"name": "is_owner", "points": 30, "passed": True},
        {"name": "is_contributor", "points": 25, "passed": True},
    ]
    assert calculate_score(checks) == 55


def test_calculate_score_ignores_failed_checks():
    from app.services.scoring import calculate_score

    checks = [
        {"name": "is_owner", "points": 30, "passed": False},
        {"name": "is_contributor", "points": 25, "passed": True},
    ]
    assert calculate_score(checks) == 25


def test_calculate_score_subtracts_negative_flags():
    from app.services.scoring import calculate_score

    checks = [
        {"name": "is_contributor", "points": 25, "passed": True},
        {"name": "all_commits_one_day", "points": -20, "passed": True},
    ]
    assert calculate_score(checks) == 5


def test_calculate_score_clamps_to_zero():
    from app.services.scoring import calculate_score

    checks = [
        {"name": "all_commits_one_day", "points": -20, "passed": True},
        {"name": "fork_of_tutorial", "points": -30, "passed": True},
    ]
    assert calculate_score(checks) == 0


def test_calculate_score_clamps_to_100():
    from app.services.scoring import calculate_score

    checks = [
        {"name": "check1", "points": 60, "passed": True},
        {"name": "check2", "points": 60, "passed": True},
    ]
    assert calculate_score(checks) == 100


def test_determine_status_verified():
    from app.services.scoring import determine_status

    assert determine_status(75) == "verified"
    assert determine_status(100) == "verified"
    assert determine_status(80) == "verified"


def test_determine_status_needs_review():
    from app.services.scoring import determine_status

    assert determine_status(45) == "needs_review"
    assert determine_status(74) == "needs_review"
    assert determine_status(60) == "needs_review"


def test_determine_status_suspicious():
    from app.services.scoring import determine_status

    assert determine_status(44) == "suspicious"
    assert determine_status(0) == "suspicious"
    assert determine_status(20) == "suspicious"
