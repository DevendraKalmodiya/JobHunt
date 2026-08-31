import os
import time
from typing import Dict, Any, Tuple
from playwright.sync_api import Page
from src.jobs import Job
from src.resume import ResumeProfile
from src.questions import QuestionHandler

class ApplicationAutomator:
    def __init__(self, page: Page, question_handler: QuestionHandler, resume_path: str = "resume/resume.pdf"):
        self.page = page
        self.qh = question_handler
        self.resume_path = os.path.abspath(resume_path)

    def process_and_submit(self, job: Job, auto_submit: bool = True, dry_run: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        # Trigger Easy Apply Modal
        apply_btn = self.page.locator("button.jobs-apply-button").first
        if not apply_btn.is_visible():
            return False, "Easy apply button not visible", {}
        apply_btn.click()
        time.sleep(2)

        answers_used = {}

        while True:
            # Check for success screen
            if self.page.locator("text='Application submitted'").is_visible() or self.page.locator(".artdeco-inline-feedback--success").is_visible():
                return True, "Application Submitted Successfully", answers_used

            # Check form fields on current step
            modal = self.page.locator(".jobs-easy-apply-modal").first
            if not modal.is_visible():
                break

            # Process file upload input
            file_inputs = modal.locator("input[type='file']").all()
            for fin in file_inputs:
                if fin.is_visible() and os.path.exists(self.resume_path):
                    fin.set_input_files(self.resume_path)
                    time.sleep(1)

            # Process Text Inputs
            form_fields = modal.locator(".jobs-easy-apply-form-section__element, .fb-dash-form-element").all()
            for field in form_fields:
                label_el = field.locator("label").first
                if not label_el.is_visible():
                    continue
                q_text = label_el.inner_text().strip()
                
                input_el = field.locator("input[type='text'], input[type='number'], textarea").first
                if input_el.is_visible() and not input_el.input_value():
                    ans = self.qh.answer_question(q_text, "text", job)
                    if ans is None:
                        print(f"\n==================================================")
                        print(f"HUMAN INTERVENTION REQUIRED")
                        print(f"Reason: UNKNOWN OR CRITICAL QUESTION: {q_text}")
                        print("Please complete field manually in browser.")
                        print("==================================================\n")
                        input("Press ENTER to resume after manual entry...")
                    else:
                        input_el.fill(ans)
                        answers_used[q_text] = ans

            # Handle Navigation Buttons
            next_btn = modal.locator("button[aria-label='Continue to next step']").first
            review_btn = modal.locator("button[aria-label='Review your application']").first
            submit_btn = modal.locator("button[aria-label='Submit application']").first

            if submit_btn.is_visible():
                if dry_run:
                    print("[DRY RUN] Stopping before clicking submit.")
                    modal.locator("button[aria-label='Dismiss']").click()
                    return True, "DRY_RUN_COMPLETED", answers_used
                elif auto_submit:
                    submit_btn.click()
                    time.sleep(3)
                    return True, "SUBMITTED", answers_used
                else:
                    input("Auto-submit disabled. Press ENTER after manual submission...")
                    return True, "MANUAL_SUBMITTED", answers_used

            if review_btn.is_visible():
                review_btn.click()
                time.sleep(1)
            elif next_btn.is_visible():
                next_btn.click()
                time.sleep(1)
            else:
                break

        return False, "Failed to navigate modal state", answers_used
