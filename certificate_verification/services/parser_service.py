import re


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def extract_name(text):
    patterns = [
        r"certificate is awarded to\s*\n?\s*(.+?)\s*\n",
        r"awarded to\s*\n?\s*(.+?)\s*\n",
        r"presented to\s*\n?\s*(.+?)\s*\n",
        r"certify that\s*\n?\s*(.+?)\s*\n"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def extract_course(text):
    patterns = [
        r"successfully completing the course\s*\n\s*(.+?)\s*\n\s*with",
        r"successfully completing the course\s*\n\s*(.+?)\s*\n\s*on",
        r"completing the course\s*\n\s*(.+?)\s*\n\s*with",
        r"completing the course\s*\n\s*(.+?)\s*\n\s*on"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            course = match.group(1).strip()

            course = re.sub(
                r"^[^A-Za-z0-9]*ty completing[^A-Za-z0-9]*",
                "",
                course,
                flags=re.IGNORECASE
            )

            return course.strip()

    return None


def extract_date(text):
    patterns = [
        r"\b([A-Za-z]{3,9})\s*[-–]?\s*([A-Za-z]{3,9})\s+(\d{4})\b",

        r"(?:on|issued on|date of issue|date)\s*:?\s*"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})",

        r"(?:on|issued on|date of issue|date)\s*:?\s*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",

        r"(?:on|issued on|date of issue|date)\s*:?\s*"
        r"([A-Za-z]+\s+\d{4})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            if len(match.groups()) == 3:
                return f"{match.group(1)}-{match.group(2)} {match.group(3)}"

            return match.group(1).strip()

    return None


def extract_certificate_id(text):
    patterns = [
        r"(?:certificate id|certificate number|certificate no\.?|credential id)"
        r"\s*:?\s*([A-Za-z0-9-]+)",

        r"Roll No:\s*([A-Za-z0-9]+)"
    ]

    invalid_values = {
        "of", "the", "is", "to", "and", "or", "for", "on", "no"
    }

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1).strip()

            if value.lower() in invalid_values:
                continue

            if len(value) < 4:
                continue

            return value

    return None


def extract_score(text):
    patterns = [
        r"consolidated score of\s*(\d+(?:\.\d+)?)\s*%",
        r"score of\s*(\d+(?:\.\d+)?)\s*%"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1) + "%"

    return None


def extract_url(text):
    match = re.search(r"https?://[^\s]+", text, re.IGNORECASE)

    if match:
        return match.group(0).rstrip(".,)")

    return None


def extract_issuer(text):
    patterns = [
        r"(?:issued by|provided by|offered by)\s+(.+?)(?:\.|,|$)",
        r"(?:organization|institution|issuer)\s*:?\s*(.+?)(?:\.|,|$)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).strip()

    known_issuers = [
        "Indian Institute of Technology Kharagpur",
        "Infosys Limited"
    ]

    for issuer in known_issuers:
        if issuer.lower() in text.lower():
            return issuer

    return None


def parse_certificate_text(text):
    text = clean_text(text)

    return {
        "name": extract_name(text),
        "course": extract_course(text),
        "date": extract_date(text),
        "certificate_id": extract_certificate_id(text),
        "issuer": extract_issuer(text),
        "score": extract_score(text),
        "verification_url": extract_url(text)
    }