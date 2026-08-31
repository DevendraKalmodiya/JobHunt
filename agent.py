import os
import sys
import time
import logging
from dotenv import load_dotenv

from src.browser import BrowserManager
from src.resume import extract_text_from_pdf
from src.gemini import GeminiClient
from src.linkedin import LinkedInEngine
from src.storage import StorageManager

# Configure console logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S"
)

def main():
    load_dotenv()
    
    print("[+] Agent starting...")
    
    # 1. Initialize Storage and Load Resume
    storage = StorageManager()
    resume_path = os.getenv("RESUME_PATH", "resume.pdf")
    
    if not os.path.exists(resume_path):
        print(f"[-] Error: Resume file not found at '{resume_path}'. Please check your .env configuration.")
        return

    print("[+] Parsing resume PDF...")
    resume_text = extract_text_from_pdf(resume_path)
    
    gemini = GeminiClient()
    profile = gemini.parse_resume(resume_text)
    
    if not profile.name:
        print("[-] Warning: Resume profile name was not extracted properly. Check API configuration.")
    else:
        print(f"[+] Resume loaded for: {profile.name}")

    # 2. Target Roles and Locations configuration
    target_roles = ["Software Engineer", "Software Developer", "AI Engineer", "Machine Learning Engineer"]
    search_locations = ["India", "Remote"]

    # 3. Initialize Playwright Browser Context
    browser = BrowserManager(user_data_dir="./browser_profile", headless=False)
    
    try:
        browser.start()

        # Guard check to satisfy Pylance static type checker
        if not browser.page:
            print("[-] Error: Browser page failed to initialize properly.")
            return

        linkedin = LinkedInEngine(browser.page)

        print("[+] Validating LinkedIn session...")
        linkedin.ensure_logged_in()
        print("[+] LinkedIn session validated.")

        # 4. Main Search and Processing Loop
        for role in target_roles:
            for location in search_locations:
                print(f"\n==================================================")
                print(f"Searching: {role} in {location}")
                print(f"==================================================")
                
                job_urls = linkedin.search_jobs(role, location)
                print(f"[+] Found {len(job_urls)} jobs to evaluate.")

                for job_url in job_urls:
                    print(f"\n[+] Inspecting: {job_url}")
                    
                    # Extract detailed job metadata
                    job = linkedin.extract_job_details(job_url)
                    
                    if not job:
                        print("  [-] Skipped: Could not extract job details or challenge encountered.")
                        continue

                    # Check for duplicate processing
                    if storage.is_processed(job.job_id, job.title, job.company):
                        print(f"  [-] Skipped (Already Processed): {job.title} at {job.company}")
                        continue

                    # Evaluate Candidate Fit using Gemini
                    match_result = gemini.match_job(profile, job, target_roles)
                    print(f"  [*] Match Score: {match_result.overall_score}% | Recommendation: {match_result.recommendation}")

                    # Decide whether to apply
                    if match_result.recommendation == "APPLY":
                        print(f"  [>] Attempting Easy Apply for: {job.title} at {job.company}...")
                        
                        # Execute application logic
                        success = linkedin.apply_to_job(job, profile, gemini, storage) if hasattr(linkedin, 'apply_to_job') else False
                        
                        if success:
                            print(f"  [✓] SUCCESS: Applied to {job.title} at {job.company}!")
                            storage.record_application(job.model_dump(), match_result.overall_score, {})
                        else:
                            print(f"  [X] FAILED/SKIPPED: Could not complete auto-application for {job.title} at {job.company}.")
                            storage.record_skipped(job.title, job.company, job.url, "Application submission failed or required complex manual steps", job.job_id)
                    else:
                        print(f"  [-] Skipped (Low Fit Score/Match): {job.title} at {job.company}")
                        storage.record_skipped(job.title, job.company, job.url, match_result.reason, job.job_id)

                    time.sleep(2)

    except KeyboardInterrupt:
        print("\n[!] Emergency Stop (Ctrl+C) triggered by user.")
    except Exception as e:
        print(f"[-] Unexpected Error: {e}")
    finally:
        print("[+] Closing browser and cleaning up...")
        browser.stop()
        print("[+] Agent execution finished cleanly.")

if __name__ == "__main__":
    main()