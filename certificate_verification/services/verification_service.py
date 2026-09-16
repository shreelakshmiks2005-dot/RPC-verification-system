import requests
from bs4 import BeautifulSoup


def verify_url(url, certificate_id=None, name=None):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return {
                "verified": False,
                "status_code": response.status_code,
                "url": url
            }

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(" ", strip=True).lower()

        id_match = False
        name_match = False

        if certificate_id:
            id_match = certificate_id.lower() in page_text

        if name:
            name_match = name.lower() in page_text

        verified = id_match or name_match

        return {
            "verified": verified,
            "status_code": response.status_code,
            "certificate_id_match": id_match,
            "name_match": name_match,
            "url": url
        }

    except requests.RequestException as e:
        return {
            "verified": False,
            "status_code": None,
            "url": url,
            "error": str(e)
        }

def verify_qr_data(qr_data, certificate_data):
    issued_to = qr_data.get("issued_to")
    course = qr_data.get("course")
    completed_on = qr_data.get("completed_on")

    ocr_name = certificate_data.get("name")
    ocr_course = certificate_data.get("course")
    ocr_date = certificate_data.get("date")

    name_match = (
        issued_to and
        ocr_name and
        issued_to.strip().lower() == ocr_name.strip().lower()
    )

    course_match = (
        course and
        ocr_course and
        course.strip().lower() == ocr_course.strip().lower()
    )

    date_match = False

    if completed_on and ocr_date:
        year = completed_on[:4]
        date_match = year in ocr_date

    verified = name_match and course_match and date_match

    return {
        "verified": verified,
        "name_match": name_match,
        "course_match": course_match,
        "date_match": date_match
    }

if __name__ == "__main__":
    qr_data = {
        "issued_to": "Shreelakshmi K S",
        "course": "Software Engineering",
        "completed_on": "2025-09-15T11:35:46Z"
    }

    certificate_data = {
        "name": "Shreelakshmi K S",
        "course": "Software Engineering",
        "date": "September 15, 2025"
    }

    result = verify_qr_data(qr_data, certificate_data)

    print(result)