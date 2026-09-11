"""
Easy Apply Screening Questions & Answers Knowledge Base
Contains answers to all 57 standard screening categories.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

# Static Profile Answers
QA_DATA = {
    # Education Details
    "highest_education": "Bachelor of Technology (B.Tech) in Computer Science with specialization in AI",
    "field_of_study": "Computer Science with specialization in Artificial Intelligence",
    "university": "Medi-Caps University, Indore",
    "cgpa": "8.39",
    
    # Location & Contact
    "location": "Indore, Madhya Pradesh, India",
    "phone": "9981405634",
    "email": "devendrakalmodiya56@gmail.com",
    
    # Language Proficiency
    "languages": "English, Hindi",
    
    # Screening & Portfolio
    "how_did_you_hear": "LinkedIn",
    "portfolio_github": "https://github.com/devendrakalmodiya",
    "why_interested": "The role matches my core skills in AI/ML, semantic search, backend APIs, and full-stack development.",
}


def get_default_answers() -> dict:
    """Returns dynamic date/time sensitive answers along with static profile answers."""
    one_week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    data = QA_DATA.copy()
    data.update({
        "notice_period_text": "Immediately",
        "notice_period_days": "0",
        "start_date": one_week_later,
        "current_salary": "0",
        "expected_salary_text": "6 LPA",
        "expected_salary_numeric": "600000",
        "experience_numeric": "0",
        "experience_text": "1 year",
    })
    return data


def resolve_text_input(label_text: str, input_type: str = "text", profile: Any = None, job: Any = None) -> str:
    """Matches text, numeric, and textarea input labels to specific QA rules."""
    text = label_text.lower()
    defaults = get_default_answers()
    is_numeric = (input_type == "number")

    # 1. Contact & Identity Information
    if any(k in text for k in ["phone", "mobile", "contact"]):
        return getattr(profile, "phone", defaults["phone"]) if profile else defaults["phone"]
    if "email" in text:
        return getattr(profile, "email", defaults["email"]) if profile else defaults["email"]
    if any(k in text for k in ["city", "location", "address", "where are you"]):
        return getattr(profile, "location", defaults["location"]) if profile else defaults["location"]

    # 2. Education Details
    if any(k in text for k in ["gpa", "cgpa", "percentage", "marks"]):
        return defaults["cgpa"]
    if any(k in text for k in ["university", "college", "school"]):
        return defaults["university"]
    if any(k in text for k in ["degree", "highest level of education"]):
        return defaults["highest_education"]
    if any(k in text for k in ["field of study", "major", "what did you study"]):
        return defaults["field_of_study"]

    # 3. Work Experience & Skills
    if any(k in text for k in ["experience", "years"]):
        return defaults["experience_numeric"] if is_numeric else defaults["experience_text"]

    # 4. Compensation / CTC
    if "current" in text and any(k in text for k in ["salary", "ctc", "pay", "compensation"]):
        return defaults["current_salary"]
    if any(k in text for k in ["expected", "desired", "requirement"]) and any(k in text for k in ["salary", "ctc", "pay", "compensation"]):
        return defaults["expected_salary_numeric"] if is_numeric else defaults["expected_salary_text"]

    # 5. Availability & Start Date
    if any(k in text for k in ["notice", "how soon"]):
        return defaults["notice_period_days"] if is_numeric else defaults["notice_period_text"]
    if any(k in text for k in ["start", "joining date", "available"]):
        return defaults["start_date"]

    # 6. Screening Questions
    if "hear about" in text or "how did you" in text:
        return defaults["how_did_you_hear"]
    if any(k in text for k in ["github", "portfolio", "website", "url"]):
        return defaults["portfolio_github"]
    if "why" in text and "interested" in text:
        return defaults["why_interested"]

    # Fallback default
    return defaults["experience_numeric"] if is_numeric else defaults["experience_text"]


def resolve_radio_selection(legend_text: str) -> str:
    """
    Determines whether to select 'Yes' or 'No' for radio groups/fieldsets.
    
    Rule Matrix:
    - Higher Degree Requirements (Master's, Ph.D.): NO
    - Non-India Authorization: NO
    - Sponsorship, Relocation, Commute, Evening/Night/Weekend Shifts, 
      Background Checks, References, Team Experience, Specific Skills: YES
    """
    text = legend_text.lower()

    # 1. Higher Education Checks
    if any(k in text for k in ["master", "doctorate", "phd", "post graduate"]):
        return "No"

    # 2. Country Specific Work Authorization
    if "authorized" in text or "legally" in text or "permit" in text:
        if any(country in text for country in ["us", "usa", "united states", "uk", "canada", "europe", "singapore", "australia"]):
            return "No"
        return "Yes"

    # 3. Default 'Yes' categories (Sponsorship, Relocation, Shifts, Background, Skills)
    if any(k in text for k in [
        "sponsorship", "require", "relocate", "commute", "onsite", "remote", "hybrid",
        "evening", "night", "weekend", "shift", "background", "reference",
        "full-time", "completed", "team", "agile", "experience", "proficient", "fluent",
        "english", "hindi", "python", "javascript", "react", "node", "rest api", "postgresql",
        "mongodb", "fastapi", "llm", "prompt", "rag", "agents", "pytorch", "tensorflow",
        "hugging face", "inference", "production", "certification", "aws"
    ]):
        return "Yes"

    # General Fallback
    return "Yes"
