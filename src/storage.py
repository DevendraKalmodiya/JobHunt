import json
import os
from datetime import datetime
from typing import Dict, Any, List

class StorageManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.apps_file = os.path.join(self.data_dir, "applications.json")
        self.skipped_file = os.path.join(self.data_dir, "skipped_jobs.json")
        self.answers_file = os.path.join(self.data_dir, "answers.json")
        
        self._ensure_files()

    def _ensure_files(self):
        for filepath in [self.apps_file, self.skipped_file]:
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
        if not os.path.exists(self.answers_file):
            default_answers = {
                "phone": "",
                "email": "",
                "city": "",
                "country": "India",
                "work_authorization": "Yes",
                "requires_sponsorship": "No"
            }
            with open(self.answers_file, "w", encoding="utf-8") as f:
                json.dump(default_answers, f, indent=2)

    def load_applications(self) -> List[Dict[str, Any]]:
        with open(self.apps_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_skipped(self) -> List[Dict[str, Any]]:
        with open(self.skipped_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_answers(self) -> Dict[str, Any]:
        with open(self.answers_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_processed(self, job_id: str, title: str, company: str) -> bool:
        apps = self.load_applications()
        skipped = self.load_skipped()
        
        for record in apps + skipped:
            # Check match by job_id if it exists and is valid
            if job_id and job_id != "Unknown" and record.get("job_id") == job_id:
                return True
            
            # Match by title and company only if both are real values (not "Unknown")
            if title != "Unknown" and company != "Unknown":
                if record.get("title") == title and record.get("company") == company:
                    return True
                    
        return False

    def record_application(self, job_data: Dict[str, Any], match_score: int, answers_used: Dict[str, Any]):
        apps = self.load_applications()
        record = {
            "job_id": job_data.get("job_id"),
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "salary_lpa": job_data.get("salary_min_lpa"),
            "match_score": match_score,
            "url": job_data.get("url"),
            "status": "APPLIED",
            "timestamp": datetime.now().isoformat(),
            "answers": answers_used
        }
        apps.append(record)
        with open(self.apps_file, "w", encoding="utf-8") as f:
            json.dump(apps, f, indent=2)

    def record_skipped(self, title: str, company: str, url: str, reason: str, job_id: str = ""):
        skipped = self.load_skipped()
        record = {
            "job_id": job_id,
            "title": title,
            "company": company,
            "url": url,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        skipped.append(record)
        with open(self.skipped_file, "w", encoding="utf-8") as f:
            json.dump(skipped, f, indent=2)