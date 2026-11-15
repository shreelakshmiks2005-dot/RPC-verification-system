"""
Resume Text Extraction Module
Extracts text from PDF and DOCX files
"""
import io
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ExtractedResume:
    raw_text: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    github_links: list[str] = field(default_factory=list)
    linkedin: Optional[str] = None


class ResumeExtractor:
    """Extracts and parses resume content from PDF/DOCX files."""

    # Common skill keywords
    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "git", "linux", "bash", "ci/cd", "jenkins", "github actions",
        "machine learning", "deep learning", "tensorflow", "pytorch", "numpy", "pandas",
        "html", "css", "sass", "tailwind", "bootstrap",
        "rest api", "graphql", "microservices", "agile", "scrum",
    }

    def __init__(self):
        pass

    async def extract_from_file(self, file_path: str) -> ExtractedResume:
        """Extract resume content from a file."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            text = await self._extract_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            text = await self._extract_docx(file_path)
        elif suffix == ".txt":
            text = await self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        return self._parse_resume(text)

    async def extract_from_bytes(self, content: bytes, filename: str) -> ExtractedResume:
        """Extract resume content from bytes."""
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            text = await self._extract_pdf_bytes(content)
        elif suffix in [".docx", ".doc"]:
            text = await self._extract_docx_bytes(content)
        elif suffix == ".txt":
            text = content.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        return self._parse_resume(text)

    async def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                return "\n".join(text_parts)
            except ImportError:
                raise ImportError("Install pdfplumber or PyPDF2: pip install pdfplumber")

    async def _extract_pdf_bytes(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(content))
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                return "\n".join(text_parts)
            except ImportError:
                raise ImportError("Install pdfplumber or PyPDF2")

    async def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

    async def _extract_docx_bytes(self, content: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

    async def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _parse_resume(self, text: str) -> ExtractedResume:
        """Parse extracted text into structured resume data."""
        resume = ExtractedResume(raw_text=text)

        # Extract email
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, text)
        if emails:
            resume.email = emails[0]

        # Extract phone
        phone_pattern = r"[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{4,6}"
        phones = re.findall(phone_pattern, text)
        if phones:
            resume.phone = phones[0]

        # Extract GitHub links
        github_pattern = r"github\.com/([a-zA-Z0-9_-]+)(?:/([a-zA-Z0-9_.-]+))?"
        github_matches = re.findall(github_pattern, text.lower())
        for match in github_matches:
            if match[1]:
                resume.github_links.append(f"https://github.com/{match[0]}/{match[1]}")
            else:
                resume.github_links.append(f"https://github.com/{match[0]}")

        # Extract LinkedIn
        linkedin_pattern = r"linkedin\.com/in/([a-zA-Z0-9_-]+)"
        linkedin_matches = re.findall(linkedin_pattern, text.lower())
        if linkedin_matches:
            resume.linkedin = f"https://linkedin.com/in/{linkedin_matches[0]}"

        # Extract skills
        text_lower = text.lower()
        found_skills = []
        for skill in self.TECH_SKILLS:
            if skill in text_lower:
                found_skills.append(skill)
        resume.skills = found_skills

        # Try to extract name (first line that looks like a name)
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            # Name heuristic: 2-4 words, mostly alphabetic
            words = line.split()
            if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
                resume.name = line
                break

        return resume
