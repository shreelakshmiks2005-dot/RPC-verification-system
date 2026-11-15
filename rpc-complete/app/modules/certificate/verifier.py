"""
Certificate Verification Module
Verifies certificate authenticity using OCR, QR codes, and online validation
"""
import httpx
from dataclasses import dataclass, field
from typing import Optional

from .extractor import CertificateExtractor, ExtractedCertificate


@dataclass
class CertificateFlag:
    type: str  # "positive", "warning", "negative"
    code: str
    message: str


@dataclass
class CertificateVerificationResult:
    score: int  # 0-100
    status: str  # "verified", "needs_review", "suspicious"
    extracted_data: ExtractedCertificate
    flags: list[CertificateFlag] = field(default_factory=list)
    online_verification: Optional[dict] = None
    details: dict = field(default_factory=dict)


class CertificateVerifier:
    """Verifies certificate authenticity."""

    # Known verification URL patterns
    VERIFICATION_DOMAINS = {
        "coursera.org": "coursera",
        "credly.com": "credly",
        "youracclaim.com": "credly",
        "udemy.com": "udemy",
        "linkedin.com": "linkedin",
        "aws.amazon.com": "aws",
        "google.com": "google",
        "microsoft.com": "microsoft",
        "verify.skilljar.com": "skilljar",
        "onwingspan.com": "infosys springboard",
        "verify.onwingspan.com": "infosys springboard",
        "infosys.com": "infosys",
        "springboard.com": "springboard",
        "nptel.ac.in": "nptel",
        "swayam.gov.in": "swayam",
        "verify.udacity.com": "udacity",
        "courses.edx.org": "edx",
    }

    def __init__(self):
        self.extractor = CertificateExtractor()

    async def verify(
        self,
        file_path: str = None,
        file_content: bytes = None,
        filename: str = None,
        expected_name: str = None,
        expected_course: str = None,
        verify_online: bool = True,
    ) -> CertificateVerificationResult:
        """
        Verify a certificate image/PDF.

        Args:
            file_path: Path to certificate file
            file_content: Raw file bytes
            filename: Original filename
            expected_name: Expected candidate name to match
            expected_course: Expected course name to match
            verify_online: Whether to attempt online verification

        Returns:
            CertificateVerificationResult with score and details
        """
        # Extract certificate data
        if file_path:
            extracted = await self.extractor.extract_from_file(file_path)
        elif file_content and filename:
            extracted = await self.extractor.extract_from_bytes(file_content, filename)
        else:
            raise ValueError("Provide either file_path or (file_content + filename)")

        flags = []
        score = 0   # Start from 0 — certificate must EARN its score
        online_verification = None

        # Check 1: Has issuer
        if extracted.issuer:
            flags.append(CertificateFlag(
                "positive", "HAS_ISSUER",
                f"Known issuer detected: {extracted.issuer}"
            ))
            score += 20  # Increased — issuer is the most important signal
        else:
            flags.append(CertificateFlag(
                "negative", "UNKNOWN_ISSUER",
                "Could not detect a known certificate issuer — may not be a valid certificate"
            ))
            score -= 5  # Small penalty for no issuer

        # Check 2: Has certificate ID
        if extracted.certificate_id:
            flags.append(CertificateFlag(
                "positive", "HAS_CERT_ID",
                f"Certificate ID found: {extracted.certificate_id}"
            ))
            score += 10
        else:
            flags.append(CertificateFlag(
                "warning", "NO_CERT_ID",
                "No certificate ID found"
            ))

        # Check 3: Has QR code
        if extracted.qr_data:
            flags.append(CertificateFlag(
                "positive", "HAS_QR",
                "QR code detected and decoded"
            ))
            score += 15  # QR is strong evidence of a real certificate

            # Check if QR contains verification URL
            if extracted.qr_data.startswith("http"):
                flags.append(CertificateFlag(
                    "positive", "QR_HAS_URL",
                    "QR code contains verification URL"
                ))
                score += 5
        else:
            flags.append(CertificateFlag(
                "warning", "NO_QR",
                "No QR code found or could not decode"
            ))

        # Check 4: Has verification URL
        if extracted.verification_url:
            domain_verified = False
            for domain, issuer in self.VERIFICATION_DOMAINS.items():
                if domain in extracted.verification_url:
                    domain_verified = True
                    flags.append(CertificateFlag(
                        "positive", "VALID_VERIFY_URL",
                        f"Verification URL from known provider: {issuer}"
                    ))
                    score += 15  # Increased — known verification domain is strong signal
                    break

            if not domain_verified:
                flags.append(CertificateFlag(
                    "warning", "UNKNOWN_VERIFY_URL",
                    "Verification URL from unknown domain"
                ))
                score += 5  # Some credit for having any verification URL

        # Check 5: Has issue date
        if extracted.issue_date:
            flags.append(CertificateFlag(
                "positive", "HAS_DATE",
                f"Issue date found: {extracted.issue_date}"
            ))
            score += 5
        else:
            flags.append(CertificateFlag(
                "warning", "NO_DATE",
                "No issue date found"
            ))

        # Check 6: Name matching (if expected name provided)
        if expected_name and extracted.candidate_name:
            name_match = self._fuzzy_name_match(
                expected_name, extracted.candidate_name
            )
            if name_match > 0.8:
                flags.append(CertificateFlag(
                    "positive", "NAME_MATCH",
                    f"Certificate name matches: {extracted.candidate_name}"
                ))
                score += 10
            elif name_match > 0.5:
                flags.append(CertificateFlag(
                    "warning", "NAME_PARTIAL_MATCH",
                    f"Certificate name partially matches: {extracted.candidate_name}"
                ))
                score += 5
            else:
                flags.append(CertificateFlag(
                    "negative", "NAME_MISMATCH",
                    f"Certificate name doesn't match. Found: {extracted.candidate_name}"
                ))
                score -= 15

        # Check 7: Course name
        if extracted.course_name:
            flags.append(CertificateFlag(
                "positive", "HAS_COURSE",
                f"Course: {extracted.course_name[:50]}"
            ))
            score += 5

        # Check 8: Text content quality
        text_length = len(extracted.raw_text.strip()) if extracted.raw_text else 0
        if text_length < 20:
            flags.append(CertificateFlag(
                "negative", "NO_TEXT",
                "Could not extract meaningful text — this may not be a certificate"
            ))
            score -= 10  # Already starts at 0, just ensure it stays low
        elif text_length < 100:
            flags.append(CertificateFlag(
                "warning", "LOW_TEXT",
                "Limited text extracted from document"
            ))
            score -= 5

        # Check 9: Online verification (if URL available and enabled)
        if verify_online and extracted.verification_url:
            online_result = await self._verify_online(extracted.verification_url)
            online_verification = online_result

            if online_result.get("verified"):
                flags.append(CertificateFlag(
                    "positive", "ONLINE_VERIFIED",
                    "Certificate verified online"
                ))
                score += 15
            elif online_result.get("accessible"):
                flags.append(CertificateFlag(
                    "warning", "ONLINE_ACCESSIBLE",
                    "Verification URL accessible but could not confirm"
                ))
            else:
                flags.append(CertificateFlag(
                    "warning", "ONLINE_FAILED",
                    "Could not access verification URL"
                ))

        # Clamp score
        score = max(0, min(100, score))

        # Determine status
        if score >= 70:
            status = "verified"
        elif score >= 40:
            status = "needs_review"
        else:
            status = "suspicious"

        # Build details
        details = {
            "text_length": text_length,
            "has_qr": bool(extracted.qr_data),
            "has_verification_url": bool(extracted.verification_url),
            "issuer_detected": bool(extracted.issuer),
        }

        return CertificateVerificationResult(
            score=score,
            status=status,
            extracted_data=extracted,
            flags=flags,
            online_verification=online_verification,
            details=details,
        )

    def _fuzzy_name_match(self, name1: str, name2: str) -> float:
        """Simple fuzzy name matching (0.0 to 1.0)."""
        # Normalize names
        n1 = name1.lower().strip().split()
        n2 = name2.lower().strip().split()

        if not n1 or not n2:
            return 0.0

        # Count matching parts
        matches = 0
        for part in n1:
            if any(part in p or p in part for p in n2):
                matches += 1

        return matches / max(len(n1), len(n2))

    async def _verify_online(self, url: str) -> dict:
        """Attempt to verify certificate online."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)

                result = {
                    "url": url,
                    "accessible": response.status_code == 200,
                    "status_code": response.status_code,
                    "verified": False,
                }

                if response.status_code == 200:
                    content = response.text.lower()
                    # Look for verification indicators
                    verified_indicators = [
                        "verified", "valid certificate", "credential verified",
                        "successfully completed", "this certifies"
                    ]
                    if any(ind in content for ind in verified_indicators):
                        result["verified"] = True

                return result

        except Exception as e:
            return {
                "url": url,
                "accessible": False,
                "error": str(e),
                "verified": False,
            }
