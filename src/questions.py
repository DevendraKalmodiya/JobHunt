from typing import Dict, Any, Optional
from src.resume import ResumeProfile
from src.jobs import Job
from src.gemini import GeminiClient

class QuestionHandler:
    def __init__(self, stored_answers: Dict[str, Any], profile: ResumeProfile, gemini_client: GeminiClient):
        self.answers = stored_answers
        self.profile = profile
        self.gemini = gemini_client

    def answer_question(self, question_text: str, field_type: str, job: Job) -> Optional[str]:
        q_lower = question_text.lower()

        # Step 1: Check answers.json matches
        if "phone" in q_lower or "mobile" in q_lower:
            return str(self.answers.get("phone", self.profile.phone))
        if "email" in q_lower:
            return str(self.answers.get("email", self.profile.email))
        if "city" in q_lower or "location" in q_lower:
            return str(self.answers.get("city", self.profile.location))
        if "sponsorship" in q_lower:
            return str(self.answers.get("requires_sponsorship", "No"))
        if "authorized" in q_lower or "legally" in q_lower:
            return str(self.answers.get("work_authorization", "Yes"))

        # Step 2: Resume exact numeric matches
        if "years" in q_lower and "experience" in q_lower:
            return str(int(self.profile.years_of_experience))

        # Step 3: Critical Classification check
        classification = self.gemini.classify_question(question_text)
        if classification.get("is_critical") or classification.get("requires_human"):
            print(f"\n[!] Critical/Unknown question encountered: '{question_text}'")
            return None

        # Step 4: AI Generation for open text
        return self.gemini.generate_application_answer(question_text, self.profile, job)
