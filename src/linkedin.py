import time
import urllib.parse
from typing import List, Optional, Any
from playwright.sync_api import Page
from src.jobs import Job
from src.utils import parse_salary_to_lpa


class LinkedInEngine:
    def __init__(self, page: Page):
        self.page = page

    def ensure_logged_in(self):
        """Navigates to LinkedIn feed and pauses for manual login/MFA if needed."""
        try:
            self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        except Exception:
            self.detect_captcha_or_mfa()

        time.sleep(3)
        if "login" in self.page.url or "signup" in self.page.url or self.page.locator("input#username").is_visible():
            print("\n==================================================")
            print("HUMAN INTERVENTION REQUIRED")
            print("Please log in to LinkedIn in the opened browser window.")
            print("Complete any MFA/Security challenges manually.")
            print("==============-====================================\n")
            input("Press ENTER here after you have logged in successfully...")

    def build_search_url(self, role: str, location: str) -> str:
        """Constructs a LinkedIn job search URL filtering for Easy Apply."""
        params = {
            "keywords": role,
            "location": location,
            "f_AL": "true",  # Easy Apply filter
            "origin": "JOB_SEARCH_PAGE_SEARCH_BUTTON"
        }
        return f"https://www.linkedin.com/jobs/search/?{urllib.parse.urlencode(params)}"

    def search_jobs(self, role: str, location: str) -> List[str]:
        """Searches for jobs matching role/location and extracts listing URLs."""
        url = self.build_search_url(role, location)
        
        try:
            self.page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
            # Handles Playwright navigation interruptions caused by checkpoint redirects
            if "checkpoint" in str(e) or "challenge" in str(e) or "interrupted" in str(e):
                self.detect_captcha_or_mfa()
                self.page.goto(url, wait_until="domcontentloaded")
            else:
                raise e

        time.sleep(3)

        # Post-load verification check
        if self.detect_captcha_or_mfa():
            self.page.goto(url, wait_until="domcontentloaded")
            time.sleep(3)

        # Collect job cards using multiple fallback selectors
        job_cards = self.page.locator(".job-card-container, .jobs-search-results__list-item, .job-card-list").all()
        job_urls = []

        for card in job_cards[:10]:
            try:
                link = card.locator("a.job-card-list__title, a.job-card-container__link, a[data-control-name='job_card_title']").first
                if link.is_visible():
                    href = link.get_attribute("href")
                    if href:
                        clean_url = href.split("?")[0]
                        if not clean_url.startswith("http"):
                            clean_url = f"https://www.linkedin.com{clean_url}"
                        job_urls.append(clean_url)
            except Exception:
                continue

        return list(set(job_urls))

    def extract_job_details(self, job_url: str) -> Optional[Job]:
        """Navigates to a specific job listing page and extracts structured detail metadata."""
        try:
            self.page.goto(job_url, wait_until="domcontentloaded")
        except Exception as e:
            if "checkpoint" in str(e) or "challenge" in str(e) or "interrupted" in str(e):
                self.detect_captcha_or_mfa()
                self.page.goto(job_url, wait_until="domcontentloaded")
            else:
                return None

        time.sleep(3)

        if self.detect_captcha_or_mfa():
            return None

        job_id = job_url.rstrip("/").split("/")[-1]

        # Extract title
        title_el = self.page.locator(
            ".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title, h1.t-24"
        ).first
        title = title_el.inner_text().strip() if title_el.is_visible() else "Unknown"

        # Extract company name
        company_el = self.page.locator(
            ".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, .job-details-jobs-unified-top-card__primary-description a"
        ).first
        company = company_el.inner_text().strip() if company_el.is_visible() else "Unknown"

        # Extract location
        loc_el = self.page.locator(
            ".job-details-jobs-unified-top-card__bullet, .jobs-unified-top-card__bullet, .job-details-jobs-unified-top-card__primary-description span"
        ).first
        location = loc_el.inner_text().strip() if loc_el.is_visible() else "Unknown"

        # Extract description body
        desc_el = self.page.locator("#job-details, .jobs-description__content, .jobs-box__html-content").first
        description = desc_el.inner_text().strip() if desc_el.is_visible() else ""

        # Extract salary text if visible on card insight
        salary_el = self.page.locator(
            ".job-details-jobs-unified-top-card__job-insight:has-text('LPA'), .jobs-unified-top-card__job-insight:has-text('₹'), .job-details-jobs-unified-top-card__job-insight:has-text('yr')"
        ).first
        salary_raw = salary_el.inner_text().strip() if salary_el.is_visible() else None

        min_lpa, max_lpa = parse_salary_to_lpa(salary_raw) if salary_raw else (None, None)

        # Validate Easy Apply availability
        easy_apply_btn = self.page.locator("button.jobs-apply-button").first
        has_easy_apply = easy_apply_btn.is_visible() and "Easy Apply" in easy_apply_btn.inner_text()

        return Job(
            job_id=job_id,
            title=title,
            company=company,
            location=location,
            salary_raw=salary_raw,
            salary_min_lpa=min_lpa,
            salary_max_lpa=max_lpa,
            description=description,
            easy_apply=has_easy_apply,
            url=job_url
        )

    def detect_captcha_or_mfa(self) -> bool:
        """Inspects page text and current URL to pause safely when security challenges appear."""
        try:
            current_url = self.page.url.lower()
            body_locator = self.page.locator("body")
            body_text = body_locator.inner_text().lower() if body_locator.is_visible() else ""
        except Exception:
            current_url = self.page.url.lower()
            body_text = ""

        if "captcha" in body_text or "security verification" in body_text or "checkpoint" in current_url or "challenge" in current_url:
            print("\n==================================================")
            print("HUMAN INTERVENTION REQUIRED")
            print("Reason: CAPTCHA / Security Verification / Checkpoint Detected.")
            print("Please complete the verification manually in the browser window.")
            print("==================================================\n")
            input("Press ENTER to continue after resolving the challenge in your browser...")
            return True
        return False

    def apply_to_job(self, job: Job, profile: Any, gemini: Any, storage: Any) -> bool:
        """Attempts to complete the Easy Apply process for a given job."""
        try:
            if not job.easy_apply:
                print("  [-] Easy Apply button not available for this listing.")
                return False

            self.page.goto(job.url, wait_until="domcontentloaded")
            time.sleep(2)

            # Click Easy Apply button
            apply_button = self.page.locator("button.jobs-apply-button").first
            if not apply_button.is_visible():
                return False

            apply_button.click()
            time.sleep(2)

            # Handle modal dialog steps
            max_steps = 10
            for _ in range(max_steps):
                if self.detect_captcha_or_mfa():
                    return False

                # Check if submission is complete
                done_button = self.page.locator("button[aria-label='Dismiss'], button:has-text('Done')").first
                if done_button.is_visible() and not self.page.locator("button:has-text('Submit application')").is_visible():
                    done_button.click()
                    return True

                # Click Submit if available
                submit_button = self.page.locator("button:has-text('Submit application')").first
                if submit_button.is_visible():
                    submit_button.click()
                    time.sleep(2)
                    return True

                # Click Next/Continue if available
                next_button = self.page.locator("button:has-text('Next'), button:has-text('Continue to application')").first
                if next_button.is_visible():
                    next_button.click()
                    time.sleep(2)
                else:
                    # If stuck on complex unhandled form field, break out
                    break

            return False
        except Exception as e:
            print(f"  [-] Application attempt failed: {e}")
            return False