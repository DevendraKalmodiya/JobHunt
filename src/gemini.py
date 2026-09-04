import os
import json
import logging
from typing import Dict, Any, List
from openai import OpenAI

from src.resume import ResumeProfile
from src.jobs import Job, JobMatchResult


class MultiProviderRouter:
    """Cloud-only AI Router (Groq & OpenRouter)."""
    def __init__(self):
        self.providers: List[Dict[str, Any]] = []

        # 1. Primary Cloud Provider: Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            self.providers.extend([
                {"name": "Groq (GPT-OSS 20B)", "client": groq_client, "model": "openai/gpt-oss-20b"}
            ])

        # 2. Secondary Cloud Router: OpenRouter Free Models
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1", 
                api_key=openrouter_key,
                default_headers={"HTTP-Referer": "http://localhost", "X-Title": "LinkedIn Agent"}
            )
            self.providers.extend([
                {"name": "OpenRouter (Gemini Flash Lite Free)", "client": openrouter_client, "model": "google/gemini-2.0-flash-lite-001:free"}
            ])

    def execute_prompt(self, prompt: str, json_mode: bool = True) -> str:
        for provider in self.providers:
            try:
                logging.info(f"Sending request via {provider['name']}...")
                kwargs = {
                    "model": provider["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = provider["client"].chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                if content.strip():
                    return content
            except Exception as e:
                logging.warning(f"Provider {provider['name']} failed/skipped: {e}. Trying next provider...")
                continue

        raise RuntimeError("All configured cloud LLM providers failed.")


class GeminiClient:
    def __init__(self):
        self.router = MultiProviderRouter()

    def parse_resume(self, raw_text: str) -> ResumeProfile:
        prompt = (
            "Extract candidate details from resume text.\n"
            "Return ONLY valid JSON matching this structure exactly:\n"
            "{\n"
            '  "name": "",\n'
            '  "email": "",\n'
            '  "phone": "",\n'
            '  "location": "",\n'
            '  "skills": [],\n'
            '  "job_titles": []\n'
            "}\n\n"
            f"Resume Text:\n{raw_text[:2500]}"
        )
        try:
            raw_json = self.router.execute_prompt(prompt, json_mode=True)
            data = json.loads(raw_json)
            return ResumeProfile(**data)
        except Exception as e:
            logging.error(f"Failed to parse resume: {e}")
            return ResumeProfile(name="Devendra Kalmodiya")

    def match_job(self, profile: ResumeProfile, job: Job, target_roles: list) -> JobMatchResult:
        prompt = (
            f"Evaluate candidate fit for the job position based on candidate resume JSON and target roles.\n"
            f"Target Roles: {target_roles}\n\n"
            f"Candidate Profile JSON:\n{profile.model_dump_json()}\n\n"
            f"Job Details:\n"
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Description: {job.description[:1500]}\n"
            f"Requirements: {job.requirements}\n\n"
            "Return ONLY valid JSON matching this exact structure:\n"
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
            raw_json = self.router.execute_prompt(prompt, json_mode=True)
            data = json.loads(raw_json)
            # Ensure APPLY recommendation if score is above threshold
            res = JobMatchResult(**data)
            if res.overall_score >= 70:
                res.recommendation = "APPLY"
            return res
        except Exception as e:
            logging.error(f"Failed to match job: {e}")
            return JobMatchResult(
                overall_score=0,
                role_match=0,
                skill_match=0,
                experience_match=0,
                education_match=0,
                location_match=0,
                matching_skills=[],
                missing_skills=[],
                concerns=["Router execution failure."],
                reason="All routed providers failed.",
                recommendation="SKIP"
            )

    def classify_question(self, question_text: str) -> Dict[str, Any]:
        prompt = (
            f'Classify this job application question: "{question_text}"\n'
            "Determine if it is a CRITICAL sensitive declaration question.\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "is_critical": true,\n'
            '  "category": "sponsorship|legal|disability|experience|general",\n'
            '  "requires_human": true\n'
            "}"
        )
        try:
            raw_json = self.router.execute_prompt(prompt, json_mode=True)
            return json.loads(raw_json)
        except Exception as e:
            return {"is_critical": True, "category": "general", "requires_human": True}

    def generate_application_answer(self, question_text: str, profile: ResumeProfile, job: Job) -> str:
        prompt = (
            "Answer the following job application question concisely based ONLY on candidate profile:\n\n"
            f"Question: {question_text}\n"
            f"Job Title: {job.title}\n"
            f"Candidate Profile:\n{profile.model_dump_json()}\n"
        )
        try:
            return self.router.execute_prompt(prompt, json_mode=False).strip()
        except Exception as e:
            return ""