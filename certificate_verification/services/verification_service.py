import os
import requests
from bs4 import BeautifulSoup
import pymupdf


def extract_official_certificate_data(pdf_path):

    document = pymupdf.open(pdf_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    certificate_data = {
        "name": None,
        "course": None,
        "date": None,
        "certificate_id": None
    }

    for line in lines:

        if line.startswith("NPTEL") and len(line) > 10:
            certificate_data["certificate_id"] = line

        if "week course" in line.lower():
            index = lines.index(line)

            if index + 1 < len(lines):
                certificate_data["course"] = lines[index + 1]

        if (
            "-" in line
            and any(char.isdigit() for char in line)
        ):
            parts = line.split()

            if len(parts) == 2:
                if "-" in parts[0] and parts[1].isdigit():
                    certificate_data["date"] = line

    for line in lines:

        if (
            line.isupper()
            and len(line.split()) >= 2
            and not line.startswith("NPTEL")
            and "ROLL" not in line
        ):
            certificate_data["name"] = line
            break

    return certificate_data


def compare_certificates(uploaded, official):

    name_match = (
        uploaded.get("name")
        and official.get("name")
        and uploaded["name"].strip().lower()
        == official["name"].strip().lower()
    )

    course_match = (
        uploaded.get("course")
        and official.get("course")
        and uploaded["course"].strip().lower()
        == official["course"].strip().lower()
    )

    date_match = (
        uploaded.get("date")
        and official.get("date")
        and uploaded["date"].strip().lower()
        == official["date"].strip().lower()
    )

    certificate_id_match = (
        uploaded.get("certificate_id")
        and official.get("certificate_id")
        and uploaded["certificate_id"].strip().lower()
        == official["certificate_id"].strip().lower()
    )

    required_fields_match = bool(
        name_match
        and course_match
        and date_match
    )

    if uploaded.get("certificate_id"):
        verified = (
            required_fields_match
            and certificate_id_match
        )
    else:
        verified = required_fields_match

    return {
        "verified": verified,
        "name_match": bool(name_match),
        "course_match": bool(course_match),
        "date_match": bool(date_match),
        "certificate_id_match": bool(certificate_id_match)
    }


def verify_nptel(url, certificate_data):

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:
            return {
                "verified": False,
                "source": "NPTEL",
                "status_code": response.status_code
            }

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        iframe = soup.find("iframe")

        if not iframe:
            return {
                "verified": False,
                "source": "NPTEL",
                "reason": "Certificate archive page not found"
            }

        archive_url = iframe.get("src")

        archive_response = requests.get(
            archive_url,
            timeout=10
        )

        if archive_response.status_code != 200:
            return {
                "verified": False,
                "source": "NPTEL",
                "status_code": archive_response.status_code
            }

        archive_soup = BeautifulSoup(
            archive_response.text,
            "html.parser"
        )

        pdf_link = archive_soup.find("a")

        if not pdf_link:
            return {
                "verified": False,
                "source": "NPTEL",
                "reason": "Official certificate PDF not found"
            }

        pdf_url = requests.compat.urljoin(
            archive_url,
            pdf_link.get("href")
        )

        pdf_response = requests.get(
            pdf_url,
            timeout=10
        )

        if pdf_response.status_code != 200:
            return {
                "verified": False,
                "source": "NPTEL",
                "status_code": pdf_response.status_code
            }

        official_pdf = "official_certificate.pdf"

        with open(
            official_pdf,
            "wb"
        ) as file:
            file.write(pdf_response.content)

        official_data = extract_official_certificate_data(
            official_pdf
        )

        result = compare_certificates(
            certificate_data,
            official_data
        )

        result["source"] = "NPTEL"
        result["source_url"] = pdf_url

        return result

    except requests.RequestException as e:

        return {
            "verified": False,
            "source": "NPTEL",
            "error": str(e)
        }


from datetime import datetime


def verify_qr_data(qr_data, certificate_data):

    issued_to = qr_data.get("issued_to")
    course = qr_data.get("course")
    completed_on = qr_data.get("completed_on")

    ocr_name = certificate_data.get("name")
    ocr_course = certificate_data.get("course")
    ocr_date = certificate_data.get("date")

    name_match = (
        issued_to
        and ocr_name
        and issued_to.strip().lower()
        == ocr_name.strip().lower()
    )

    course_match = (
        course
        and ocr_course
        and course.strip().lower()
        == ocr_course.strip().lower()
    )

    date_match = False

    if completed_on and ocr_date:

        try:
            qr_date = datetime.fromisoformat(
                completed_on.replace("Z", "+00:00")
            ).date()

            ocr_date_object = datetime.strptime(
                ocr_date.strip(),
                "%B %d, %Y"
            ).date()

            date_match = (
                qr_date == ocr_date_object
            )

        except ValueError:
            date_match = False

    verified = (
        bool(name_match)
        and bool(course_match)
        and bool(date_match)
    )

    return {
        "verified": verified,
        "name_match": bool(name_match),
        "course_match": bool(course_match),
        "date_match": bool(date_match)
    }


def verify_official_source(
    url,
    certificate_data
):

    if "nptel.ac.in" in url.lower():
        return verify_nptel(
            url,
            certificate_data
        )

    return {
        "verified": False,
        "source": "Unknown",
        "reason": "Official source verification not implemented for this URL"
    }

if __name__ == "__main__":

    certificate_data = {
        "name": "ABDUL ALEEM",
        "course": "Fake Course",
        "date": "Jul-Oct 2023",
        "certificate_id": "NPTEL23CS92S637401244"
    }

    url = "https://nptel.ac.in/noc/E_Certificate/NPTEL23CS92S63740124420075591"

    result = verify_official_source(
        url,
        certificate_data
    )

    print(result)