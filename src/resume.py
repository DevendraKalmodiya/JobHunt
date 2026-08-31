from typing import List, Optional
from pydantic import BaseModel, Field
import pymupdf  # Clean modern PyMuPDF import


class ResumeProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    education: List[dict] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    projects: List[dict] = Field(default_factory=list)
    internships: List[dict] = Field(default_factory=list)
    work_experience: List[dict] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    job_titles: List[str] = Field(default_factory=list)
    years_of_experience: float = 0.0


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    try:
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)
    finally:
        doc.close()