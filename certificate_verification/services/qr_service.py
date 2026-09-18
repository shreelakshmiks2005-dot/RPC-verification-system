import cv2
import json
import pymupdf
import numpy as np
from pyzbar.pyzbar import decode


def process_qr(qr):
    data = qr.data.decode("utf-8").strip()

    try:
        qr_data = json.loads(data)

        credential_subject = qr_data.get(
            "credentialSubject", {}
        )

        proof = qr_data.get(
            "proof", {}
        )

        return {
            "type": "verifiable_credential",
            "raw_data": data,
            "issued_to": credential_subject.get("issuedTo"),
            "course": credential_subject.get("course"),
            "completed_on": credential_subject.get("completedOn"),
            "issuer": qr_data.get("issuer"),
            "proof_type": proof.get("type"),
            "verification_method": proof.get(
                "verificationMethod"
            )
        }

    except json.JSONDecodeError:

        return {
            "type": "url",
            "raw_data": data,
            "url": data
        }


def decode_image(image):

    images = [image]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    images.append(gray)

    for scale in [2, 3, 4]:

        height, width = gray.shape

        resized = cv2.resize(
            gray,
            (width * scale, height * scale),
            interpolation=cv2.INTER_CUBIC
        )

        images.append(resized)

        _, threshold = cv2.threshold(
            resized,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        images.append(threshold)

    results = []

    for img in images:

        qr_codes = decode(img)

        for qr in qr_codes:

            result = process_qr(qr)

            if result not in results:
                results.append(result)

    return results


def decode_qr(image_path):

    results = []

    if image_path.lower().endswith(".pdf"):

        document = pymupdf.open(image_path)

        for page in document:

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(3, 3)
            )

            image_bytes = pixmap.tobytes("png")

            image_array = np.frombuffer(
                image_bytes,
                dtype=np.uint8
            )

            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            page_results = decode_image(image)

            for result in page_results:

                if result not in results:
                    results.append(result)

        document.close()

    else:

        image = cv2.imread(image_path)

        if image is None:
            return []

        results = decode_image(image)

    return results