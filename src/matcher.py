from typing import Tuple
from src.jobs import Job, JobMatchResult
from src.resume import ResumeProfile
from src.gemini import GeminiClient

class JobMatcher:
    def __init__(self, config: dict, gemini_client: GeminiClient):
        self.config = config
        self.gemini = gemini_client
        self.min_salary = config.get("minimum_salary_lpa", 3.0)
        self.min_score = config.get("minimum_match_score", 70)
        self.skip_unknown_salary = config.get("skip_if_salary_unknown", True)
        self.exclusion_keywords = [k.lower() for k in config.get("exclusion_keywords", [])]

    def evaluate_job(self, job: Job, profile: ResumeProfile) -> Tuple[bool, str, int]:
        # Rule 1: Exclusion Keywords
        for kw in self.exclusion_keywords:
            if kw in job.title.lower():
                return False, f"Exclusion keyword found in title: '{kw}'", 0

        # Rule 2: Salary Filter
        if job.salary_min_lpa is not None:
            if job.salary_min_lpa < self.min_salary:
                return False, f"Salary ({job.salary_min_lpa} LPA) below minimum threshold ({self.min_salary} LPA)", 0
        elif self.skip_unknown_salary:
            return False, "Salary unknown and skip_if_salary_unknown is enabled", 0

        # Rule 3: AI Matching via Gemini
        match_result: JobMatchResult = self.gemini.match_job(profile, job, self.config.get("target_roles", []))
        
        if match_result.overall_score < self.min_score:
            return False, f"AI Match score ({match_result.overall_score}) below threshold ({self.min_score})", match_result.overall_score

        if match_result.recommendation.upper() == "SKIP":
            return False, f"AI Recommendation SKIP: {match_result.reason}", match_result.overall_score

        return True, "Job passed all criteria", match_result.overall_score
