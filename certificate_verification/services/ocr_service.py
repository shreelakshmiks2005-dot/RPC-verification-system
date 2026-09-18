import cv2
import pytesseract
import pymupdf

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(file_path):

    if file_path.lower().endswith(".pdf"):

        document = pymupdf.open(file_path)

        text = ""

        for page in document:

            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

            image = pixmap.tobytes("png")

            import numpy as np

            image_array = np.frombuffer(image, dtype=np.uint8)

            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            gray = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY
            )

            text += pytesseract.image_to_string(gray)

        document.close()

        return text

    image = cv2.imread(file_path)

    if image is None:
        raise ValueError("Unable to read the image")

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return pytesseract.image_to_string(gray)