import os
import json
import logging
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from src.resume import ResumeProfile
from src.jobs import Job, JobMatchResult


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3.6-flash"

    def parse_resume(self, raw_text: str) -> ResumeProfile:
        prompt = (
            "Extract structured information from the following resume text.\n"
            "Return ONLY valid JSON matching this structure:\n"
            "{\n"
            '  "name": "",\n'
            '  "email": "",\n'
            '  "phone": "",\n'
            '  "location": "",\n'
            '  "education": [],\n'
            '  "skills": [],\n'
            '  "programming_languages": [],\n'
            '  "frameworks": [],\n'
            '  "tools": [],\n'
            '  "projects": [],\n'
            '  "internships": [],\n'
            '  "work_experience": [],\n'
            '  "certifications": [],\n'
            '  "achievements": [],\n'
            '  "job_titles": [],\n'
            '  "years_of_experience": 0.0\n'
            "}\n\n"
            f"Resume Text:\n{raw_text}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_json = response.text or "{}"
            data = json.loads(raw_json)
            return ResumeProfile(**data)
        except Exception as e:
            logging.error(f"Failed to parse resume via Gemini: {e}")
            return ResumeProfile()

    def match_job(self, profile: ResumeProfile, job: Job, target_roles: list) -> JobMatchResult:
        prompt = (
            f"Evaluate candidate fit for the job position based on candidate resume JSON and target roles.\n"
            f"Target Roles: {target_roles}\n\n"
            f"Candidate Profile JSON:\n{profile.model_dump_json()}\n\n"
            f"Job Details:\n"
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Description: {job.description}\n"
            f"Requirements: {job.requirements}\n\n"
            "Return ONLY valid JSON with structure:\n"
            "{\n"
            '  "overall_score": 85,\n'
            '  "role_match": 90,\n'
            '  "skill_match": 80,\n'
            '  "experience_match": 80,\n'
            '  "education_match": 90,\n'
            '  "location_match": 100,\n'
            '  "matching_skills": ["Python"],\n'
            '  "missing_skills": [],\n'
            '  "concerns": [],\n'
            '  "reason": "Strong match.",\n'
            '  "recommendation": "APPLY"\n'
            "}\n"
            'Recommendation options: "APPLY", "SKIP", "REVIEW"'
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_json = response.text or "{}"
            data = json.loads(raw_json)
            return JobMatchResult(**data)
        except Exception as e:
            logging.error(f"Failed to match job via Gemini: {e}")
            return JobMatchResult(
                overall_score=0,
                role_match=0,
                skill_match=0,
                experience_match=0,
                education_match=0,
                location_match=0,
                matching_skills=[],
                missing_skills=[],
                concerns=[str(e)],
                reason="API Error during job matching.",
                recommendation="SKIP"
            )

    def classify_question(self, question_text: str) -> Dict[str, Any]:
        prompt = (
            f'Classify this job application question: "{question_text}"\n'
            "Determine if it is a CRITICAL sensitive declaration question.\n"
            "Critical questions include: legal authorization, visa sponsorship, criminal/legal declarations, disability status, veteran status, legal agreement declarations.\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "is_critical": true,\n'
            '  "category": "sponsorship|legal|disability|experience|general",\n'
            '  "requires_human": true\n'
            "}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_json = response.text or "{}"
            return json.loads(raw_json)
        except Exception as e:
            logging.error(f"Failed to classify question via Gemini: {e}")
            return {"is_critical": True, "category": "general", "requires_human": True}

    def generate_application_answer(self, question_text: str, profile: ResumeProfile, job: Job) -> str:
        prompt = (
            "Answer the following job application question accurately and concisely based ONLY on the candidate profile. Do NOT lie or fabricate credentials.\n\n"
            f"Question: {question_text}\n"
            f"Job Title: {job.title}\n"
            f"Company: {job.company}\n\n"
            f"Candidate Profile:\n{profile.model_dump_json()}\n\n"
            "Provide a short direct answer suitable for a form field."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text_val = response.text or ""
            return text_val.strip()
        except Exception as e:
            logging.error(f"Failed to generate application answer via Gemini: {e}")
            return ""