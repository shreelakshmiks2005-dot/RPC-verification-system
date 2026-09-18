def calculate_certificate_score(verification):
    score = 0

    if verification.get("verified"):
        score += 40

    if verification.get("name_match"):
        score += 20

    if verification.get("course_match"):
        score += 15

    if verification.get("date_match"):
        score += 15

    if verification.get("certificate_id_match"):
        score += 10

    return score