from typing import List, Optional
from pydantic import BaseModel, Field
import pymupdf  # Clean modern PyMuPDF import


class ResumeProfile(BaseModel):
    # Personal & Contact Information
    name: str = "DEVENDRA KALMODIYA"
    email: str = "devendrakalmodiya56@gmail.com"
    phone: str = "9981405634"
    location: str = "Indore, India"
    
    # Common Easy Apply Application Question Defaults
    total_experience_years: str = "1"
    notice_period_days: str = "0"          # Immediate joiner
    expected_salary: str = "Negotiable"
    legally_authorized: str = "Yes"
    require_sponsorship: str = "No"
    willing_to_relocate: str = "Yes"
    background_check: str = "Yes"

    # Education Details
    education: List[dict] = Field(default_factory=lambda: [
        {
            "degree": "Bachelor of Technology in Computer Science (AI)",
            "institution": "Medi-Caps University, Indore",
            "cgpa": "8.39",
            "duration": "2023-2027"
        },
        {
            "degree": "Class 12th (PCM)",
            "institution": "Ebenezer English Higher Secondary School, Mandsaur",
            "percentage": "71.24%",
            "year": "2022-2023"
        },
        {
            "degree": "Class 10th",
            "institution": "St. Thomas Sr Sec School, Mandsaur",
            "percentage": "82.2%",
            "year": "2020-2021"
        }
    ])

    # Categorized Technical Skills
    skills: List[str] = Field(default_factory=lambda: [
        "Python", "JavaScript", "React.js", "Node.js", "Express.js", 
        "PostgreSQL", "MongoDB", "MySQL", "C++", "Java", "Tailwind CSS",
        "Artificial Intelligence", "Machine Learning", "Semantic Search", 
        "Vector Databases", "Git", "GitHub", "AWS", "REST APIs"
    ])
    programming_languages: List[str] = Field(default_factory=lambda: [
        "Java", "JavaScript", "Python", "C++"
    ])
    frameworks: List[str] = Field(default_factory=lambda: [
        "React.js", "Tailwind", "Node.js", "Express.js"
    ])
    tools: List[str] = Field(default_factory=lambda: [
        "Git", "GitHub", "Postman", "Supabase", "Vercel", "Render", "Cloudinary", "Figma"
    ])

    # Projects & Experience
    projects: List[dict] = Field(default_factory=lambda: [
        {
            "name": "Placeaura",
            "tech": ["React", "Node.js", "PostgreSQL", "Supabase", "Gemini API"],
            "description": "AI-powered job matching platform using semantic search and vector similarity with PostgreSQL (pgvector) and Supabase."
        },
        {
            "name": "InstructorIndex",
            "tech": ["React", "Node.js", "Express.js", "MongoDB", "Cloudinary"],
            "description": "Full-stack LMS supporting instructors and students with secure role-based access control and JWT authentication."
        }
    ])
    internships: List[dict] = Field(default_factory=lambda: [
        {
            "role": "Full Stack Developer Intern / Junior Manager",
            "company": "SWET",
            "description": "Led a 5-member team to develop the organization's website, integrating React frontend with Node.js APIs."
        },
        {
            "role": "ML Intern",
            "company": "IQpath Technologies Pvt Ltd",
            "description": "Built and deployed ML models for semantic data understanding, migrated data to PostgreSQL with pgvector for vector search."
        }
    ])
    work_experience: List[dict] = Field(default_factory=lambda: [
        {
            "role": "Chief of Outgoing Global Corporate",
            "organization": "AIESEC",
            "description": "Managed 20+ international partnerships across Europe, MENA, and Asia. Led a 17-member team."
        }
    ])

    # Certifications & Achievements
    certifications: List[str] = Field(default_factory=lambda: [
        "Deloitte Data Analytics Job Simulation",
        "JP Morgan Chase & Co. Software Engineering Job Simulation",
        "Amazon AWS Cloud Foundations",
        "LeetCode SQL 50 Badge",
        "Infrabuild: AWS Mastery",
        "Advanced Data Structures and Algorithms - Board Infinity"
    ])
    achievements: List[str] = Field(default_factory=lambda: [
        "Best Delegate, AIESEC National Bootcamp",
        "Bronze in National level Hockey tournament (North West Zone India)",
        "3rd position at Physics Exhibition, Medi-Caps University"
    ])
    
    # Target Roles & Numerical Attributes
    job_titles: List[str] = Field(default_factory=lambda: [
        "Full Stack Developer", "Software Engineer", "Frontend Developer", "ML Intern"
    ])
    years_of_experience: int = 0


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text content from a target PDF file using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    try:
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        return "\n".join(pages)
    finally:
        doc.close()