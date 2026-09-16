import cv2
import json
from pyzbar.pyzbar import decode


def process_qr(qr):
    data = qr.data.decode("utf-8")

    try:
        qr_data = json.loads(data)

        credential_subject = qr_data.get("credentialSubject", {})
        proof = qr_data.get("proof", {})

        return {
            "issued_to": credential_subject.get("issuedTo"),
            "course": credential_subject.get("course"),
            "completed_on": credential_subject.get("completedOn"),
            "issuer": qr_data.get("issuer"),
            "proof_type": proof.get("type"),
            "verification_method": proof.get("verificationMethod")
        }

    except json.JSONDecodeError:
        return {
            "data": data
        }


def decode_qr(image_path):
    image = cv2.imread(image_path)

    if image is None:
        return []

    images = []

    images.append(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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


if __name__ == "__main__":
    result = decode_qr("uploads/sample1.jpg")
    print(result)