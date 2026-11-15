"""
Certificate Data Extraction Module
OCR and QR Code extraction from certificate images
"""
import io
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ExtractedCertificate:
    raw_text: str
    candidate_name: Optional[str] = None
    issuer: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    certificate_id: Optional[str] = None
    qr_data: Optional[str] = None
    verification_url: Optional[str] = None


class CertificateExtractor:
    """Extracts data from certificate images using OCR and QR decoding."""

    # Known certificate issuers
    KNOWN_ISSUERS = [
        "coursera", "udemy", "linkedin learning", "pluralsight",
        "aws", "amazon web services", "google cloud", "microsoft",
        "azure", "oracle", "cisco", "comptia", "pmi", "scrum.org",
        "mongodb", "redis", "hashicorp", "kubernetes", "cncf",
        "meta", "facebook", "google", "ibm", "salesforce",
        "infosys", "infosys springboard", "springboard", "wingspan",
        "onwingspan", "wipro", "tcs", "accenture", "cognizant",
        "nptel", "swayam", "udacity", "edx", "codecademy",
        "freecodecamp", "hackerrank", "leetcode",
    ]

    def __init__(self):
        pass

    async def extract_from_file(self, file_path: str) -> ExtractedCertificate:
        """Extract certificate data from an image file."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            return await self._extract_from_image_file(file_path)
        elif suffix == ".pdf":
            return await self._extract_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    async def extract_from_bytes(
        self, content: bytes, filename: str
    ) -> ExtractedCertificate:
        """Extract certificate data from image bytes."""
        suffix = Path(filename).suffix.lower()

        if suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            return await self._extract_from_image_bytes(content)
        elif suffix == ".pdf":
            return await self._extract_from_pdf_bytes(content)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    async def _extract_from_image_file(self, file_path: str) -> ExtractedCertificate:
        """Extract from image file using OCR."""
        try:
            from PIL import Image
            image = Image.open(file_path)
            return await self._process_image(image)
        except ImportError:
            raise ImportError("Install Pillow: pip install Pillow")

    async def _extract_from_image_bytes(self, content: bytes) -> ExtractedCertificate:
        """Extract from image bytes using OCR."""
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(content))
            return await self._process_image(image)
        except ImportError:
            raise ImportError("Install Pillow: pip install Pillow")

    async def _extract_from_pdf(self, file_path: str) -> ExtractedCertificate:
        """Extract from PDF file (first page as image)."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            page = doc[0]
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()

            from PIL import Image
            image = Image.open(io.BytesIO(img_data))
            return await self._process_image(image)
        except ImportError:
            # Fallback: try pdfplumber for text only
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = pdf.pages[0].extract_text() or ""
                return self._parse_certificate_text(text, qr_data=None)
            except ImportError:
                raise ImportError("Install PyMuPDF: pip install PyMuPDF")

    async def _extract_from_pdf_bytes(self, content: bytes) -> ExtractedCertificate:
        """Extract from PDF bytes — text extraction + QR from rendered image."""
        text = ""
        qr_data = None

        # Step 1: Try pdfplumber for text
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = pdf.pages[0].extract_text() or ""
        except Exception:
            pass

        # Step 2: Render PDF page as image for QR decoding (always do this)
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()

            from PIL import Image
            image = Image.open(io.BytesIO(img_data))

            # Always try QR decode from rendered image
            qr_data = self._decode_qr(image)

            # If no text from pdfplumber, try OCR on image
            if len(text.strip()) < 30:
                text = self._ocr_image(image)

        except Exception:
            pass

        return self._parse_certificate_text(text, qr_data)

    async def _process_image(self, image) -> ExtractedCertificate:
        """Process image: OCR + QR code extraction."""
        # Extract QR code
        qr_data = self._decode_qr(image)

        # Extract text via OCR
        text = self._ocr_image(image)

        return self._parse_certificate_text(text, qr_data)

    def _decode_qr(self, image) -> Optional[str]:
        """Decode QR code from image."""
        try:
            from pyzbar.pyzbar import decode
            decoded = decode(image)
            if decoded:
                return decoded[0].data.decode("utf-8")
        except ImportError:
            pass  # pyzbar not installed
        except Exception:
            pass  # QR decode failed
        return None

    def _ocr_image(self, image) -> str:
        """Perform OCR on image."""
        try:
            import pytesseract
            import os
            import sys

            # Auto-detect Tesseract on Windows if not in PATH
            if sys.platform == 'win32' and not pytesseract.pytesseract.tesseract_cmd:
                candidates = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
                ]
                for path in candidates:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break

            text = pytesseract.image_to_string(image)
            return text
        except ImportError:
            return ""
        except Exception as e:
            # Tesseract binary not found — return empty string gracefully
            return ""

    def _parse_certificate_text(
        self, text: str, qr_data: Optional[str]
    ) -> ExtractedCertificate:
        """Parse extracted text into structured certificate data."""
        cert = ExtractedCertificate(raw_text=text, qr_data=qr_data)

        text_lower = text.lower()

        # Extract issuer
        for issuer in self.KNOWN_ISSUERS:
            if issuer in text_lower:
                cert.issuer = issuer.title()
                break

        # Extract dates
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
            r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
            r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
        ]

        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates_found.extend(matches)

        if dates_found:
            cert.issue_date = dates_found[0]
            if len(dates_found) > 1:
                cert.expiry_date = dates_found[1]

        # Extract certificate ID
        id_patterns = [
            r"certificate\s*(?:id|#|no\.?|number)[\s:]*([A-Z0-9-]+)",
            r"credential\s*id[\s:]*([A-Z0-9-]+)",
            r"id[\s:]*([A-Z0-9]{8,})",
        ]

        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cert.certificate_id = match.group(1)
                break

        # Extract verification URL — catch both /verify paths and known verify domains
        url_pattern = r"(https?://[^\s]+)"
        for url_match in re.finditer(url_pattern, text, re.IGNORECASE):
            url = url_match.group(1).rstrip('.,)')
            if any(kw in url.lower() for kw in ["verify", "credential", "certificate", "onwingspan", "acclaim", "credly"]):
                cert.verification_url = url
                break
        if not cert.verification_url and qr_data and qr_data.startswith("http"):
            cert.verification_url = qr_data

        # Try to extract course name
        course_patterns = [
            r"completing\s+the\s+course\s*[\n\r]+([^\n\r]+)",   # "completing the course\nIntroduction to Python"
            r"(?:course|certification|certificate)[\s:]+([^\n]+)",
            r"has\s+(?:successfully\s+)?completed[\s:]+([^\n]+)",
            r"for\s+(?:successfully\s+)?completing[\s:]+([^\n]+)",
        ]

        for pattern in course_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:  # skip garbage matches
                    cert.course_name = name[:100]
                    break

        # Try to extract name — supports 2 or 3 word names (e.g. "Tarun K V")
        name_patterns = [
            r"this\s+(?:is\s+to\s+)?certif(?:y|ies)\s+that\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*){1,3})",
            r"awarded\s+to[\s:]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*){1,3})",
            r"presented\s+to[\s:]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*){1,3})",
            r"certificate\s+is\s+awarded\s+to[\s\n]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*){1,3})",
            r"name[\s:]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]*){1,3})",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                cert.candidate_name = match.group(1).strip()
                break

        return cert
