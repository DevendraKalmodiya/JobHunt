from typing import Optional, List
from pydantic import BaseModel, Field

class Job(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    salary_raw: Optional[str] = None
    salary_min_lpa: Optional[float] = None
    salary_max_lpa: Optional[float] = None
    description: str
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    easy_apply: bool = True
    url: str
    posted_date: Optional[str] = None

class JobMatchResult(BaseModel):
    overall_score: int
    role_match: int
    skill_match: int
    experience_match: int
    education_match: int
    location_match: int
    matching_skills: List[str]
    missing_skills: List[str]
    concerns: List[str]
    reason: str
    recommendation: str
