import time
import logging
from typing import List, Optional, Any, Dict
from src.jobs import Job


class LinkedInEngine:
    def __init__(self, page: Any):
        self.page = page

    # ==========================================
    # PHASE 5: BROWSER/CONTEXT LIFECYCLE GUARDS
    # ==========================================
    def is_browser_alive(self) -> bool:
        """Verifies if the browser context and underlying page are open."""
        return self.page is not None and not self.page.is_closed()

    def ensure_logged_in(self) -> bool:
        """Validates that an active LinkedIn session exists."""
        if not self.is_browser_alive():
            return False

        try:
            self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)

            if "login" in self.page.url or "checkpoint" in self.page.url:
                logging.error("LinkedIn session invalid or expired. Manual login required.")
                return False

            nav_element = self.page.locator(".global-nav, .search-global-typeahead, #global-nav").first
            return nav_element.is_visible()
        except Exception as e:
            logging.error(f"Failed session validation: {e}")
            return False

    # ==========================================
    # PHASE 1: LINKEDIN PAGE LOADING & HARVESTING
    # ==========================================
    def search_jobs(self, keywords: str, location: str) -> List[str]:
        """Performs job search and returns cleaned job URLs."""
        if not self.is_browser_alive():
            return []

        search_url = (
            f"https://www.linkedin.com/jobs/search/?"
            f"keywords={keywords.replace(' ', '%20')}&"
            f"location={location.replace(' ', '%20')}&"
            f"f_AL=true"  # Easy Apply Filter
        )
        try:
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
        except Exception as e:
            logging.error(f"Search navigation failed: {e}")
            return []

        job_urls = []
        try:
            self.page.wait_for_selector(".job-card-container, .job-card-list__title", timeout=10000)
            card_links = self.page.locator("a.job-card-container__link, a.job-card-list__title").all()
            for link in card_links:
                href = link.get_attribute("href")
                if href and "/jobs/view/" in href:
                    clean_url = href.split("?")[0]
                    if not clean_url.startswith("https://"):
                        clean_url = f"https://www.linkedin.com{clean_url}"
                    if clean_url not in job_urls:
                        job_urls.append(clean_url)
        except Exception as e:
            logging.warning(f"Failed to harvest job cards: {e}")

        return job_urls

    # ==========================================
    # PHASE 2: JOB TITLE + COMPANY EXTRACTION
    # ==========================================
    def extract_job_details(self, job_url: str) -> Optional[Job]:
        if not self.is_browser_alive():
            return None

        try:
            self.page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Failed loading job view for {job_url}: {e}")
            return None

        if not self.is_browser_alive():
            return None

        job_id = job_url.rstrip("/").split("/")[-1]

        try:
            self.page.evaluate("window.scrollBy(0, 250)")
            time.sleep(1)
        except Exception:
            pass

        title = "Unknown"
        title_selectors = [
            "h1.job-details-jobs-unified-top-card__job-title",
            ".job-details-jobs-unified-top-card__job-title",
            ".jobs-unified-top-card__job-title",
            "h1.t-24",
            "h1"
        ]
        for sel in title_selectors:
            try:
                el = self.page.locator(sel).first
                if el.is_visible():
                    t_text = el.inner_text().strip()
                    if t_text and t_text != "Unknown":
                        title = t_text
                        break
            except Exception:
                continue

        company = "Unknown"
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name",
            ".job-details-jobs-unified-top-card__primary-description a",
            "a.jobs-unified-top-card__company-name",
            ".jobs-company__name"
        ]
        for sel in company_selectors:
            try:
                el = self.page.locator(sel).first
                if el.is_visible():
                    c_text = el.inner_text().strip()
                    if c_text and c_text != "Unknown":
                        company = c_text
                        break
            except Exception:
                continue

        try:
            doc_title = self.page.title()
            if "|" in doc_title:
                parts = [p.strip() for p in doc_title.split("|")]
                if len(parts) >= 2:
                    if title == "Unknown":
                        title = parts[0]
                    if company == "Unknown" and parts[1] != "LinkedIn":
                        company = parts[1]
            elif " hiring " in doc_title:
                parts = doc_title.split(" hiring ")
                company = parts[0].strip() if company == "Unknown" else company
                remainder = parts[1].split(" in ")[0] if " in " in parts[1] else parts[1].split(" | ")[0]
                title = remainder.strip() if title == "Unknown" else title
        except Exception:
            pass

        detection = self.detect_easy_apply_button(run_diagnostics=False)
        has_easy_apply = detection["is_easy_apply"]

        desc_text = ""
        try:
            desc_el = self.page.locator("#job-details, .jobs-description__content").first
            if desc_el.is_visible():
                desc_text = desc_el.inner_text().strip()
        except Exception:
            pass

        return Job(
            job_id=job_id,
            title=title,
            company=company,
            location="India",
            salary_raw=None,
            salary_min_lpa=None,
            salary_max_lpa=None,
            description=desc_text,
            easy_apply=has_easy_apply,
            url=job_url
        )

    # ==========================================
    # PHASE 3: EASY APPLY DETECTION ENGINE
    # ==========================================
    def detect_easy_apply_button(self, run_diagnostics: bool = True) -> Dict[str, Any]:
        """Detects Easy Apply presence checking ARIA labels, hrefs, and buttons across page & iFrames."""
        result = {
            "is_easy_apply": False,
            "is_external_apply": False,
            "button_handle": None,
            "strategy": None
        }

        if not self.is_browser_alive():
            return result

        if run_diagnostics:
            try:
                clickable_els = self.page.locator("button, a[aria-label*='Easy Apply'], a.jobs-apply-button, a[href*='/apply/']").all()
                apply_texts = []
                easy_apply_texts = []

                for el in clickable_els:
                    try:
                        txt = el.inner_text().strip() or el.get_attribute("aria-label") or ""
                        if txt:
                            if "apply" in txt.lower():
                                apply_texts.append(txt)
                            if "easy apply" in txt.lower():
                                easy_apply_texts.append(txt)
                    except Exception:
                        continue

                print("\n  === EASY APPLY DIAGNOSTICS ===")
                print(f"  Current URL              : {self.page.url}")
                print(f"  Page title               : {self.page.title()}")
                print(f"  Interactive Elements     : {len(clickable_els)}")
                print(f"  Elements with 'Apply'    : {apply_texts}")
                print(f"  Elements with 'Easy Apply': {easy_apply_texts}")
                print("  ================================\n")
            except Exception as e:
                print(f"  [-] Diagnostics gathering warning: {e}")

        # Comprehensive selectors targeting both <button> and <a> tag implementations
        easy_apply_selectors = [
            "button:has-text('Easy Apply')",
            "a[aria-label*='Easy Apply']",
            "a[href*='/apply/']",
            "button[aria-label*='Easy Apply']",
            "a:has-text('Easy Apply')",
            ".jobs-apply-button--top-card button",
            ".jobs-apply-button",
            "button.jobs-apply-button"
        ]

        # 1. Scan Main Frame
        for sel in easy_apply_selectors:
            try:
                handle = self.page.locator(sel).first
                if handle.is_visible():
                    result.update({
                        "is_easy_apply": True, 
                        "button_handle": handle, 
                        "strategy": f"Main Frame ({sel})"
                    })
                    return result
            except Exception:
                continue

        # 2. Scan iFrames
        try:
            for frame in self.page.frames:
                for sel in easy_apply_selectors:
                    try:
                        handle = frame.locator(sel).first
                        if handle.is_visible():
                            result.update({
                                "is_easy_apply": True, 
                                "button_handle": handle, 
                                "strategy": f"iFrame [{frame.name}] ({sel})"
                            })
                            return result
                    except Exception:
                        continue
        except Exception:
            pass

        # 3. Check for External Apply
        external_selectors = ["button:has-text('Apply')", "a:has-text('Apply')"]
        for sel in external_selectors:
            try:
                handle = self.page.locator(sel).first
                if handle.is_visible():
                    txt = handle.inner_text().lower()
                    if "easy apply" not in txt:
                        result.update({"is_external_apply": True, "strategy": f"External ({sel})"})
                        return result
            except Exception:
                continue

        return result

    # ==========================================
    # PHASE 4: EASY APPLY FORM INTERACTION
    # ==========================================
    def apply_to_job(self, job: Job, profile: Any, gemini: Any, storage: Any) -> bool:
        if not self.is_browser_alive():
            return False

        try:
            if self.page.url != job.url:
                self.page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(2)

            if not self.is_browser_alive():
                return False

            detection = self.detect_easy_apply_button(run_diagnostics=True)

            if detection["is_external_apply"]:
                print("  [-] External Apply detected (Redirects off-site). Skipping auto-application.")
                return False

            if not detection["is_easy_apply"] or not detection["button_handle"]:
                print("  [-] Easy Apply button not present on loaded page.")
                return False

            print(f"  [+] Easy Apply button located using: {detection['strategy']}")
            apply_btn = detection["button_handle"]
            
            # Click application trigger (may cause page navigation for <a> links)
            apply_btn.click()
            time.sleep(3)

            # Form Modal & Full-Page Flow Interaction Loop
            for step in range(12):
                if not self.is_browser_alive():
                    return False

                # Handle Done / Completion
                done_btn = self.page.locator("button[aria-label='Dismiss'], button:has-text('Done'), a:has-text('Done')").first
                if done_btn.is_visible() and not self.page.locator("button:has-text('Submit application'), button:has-text('Submit')").is_visible():
                    done_btn.click()
                    return True

                # Submit Application
                submit_btn = self.page.locator("button:has-text('Submit application'), button:has-text('Submit')").first
                if submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(2)
                    return True

                # Next / Continue Step
                next_btn = self.page.locator("button:has-text('Next'), button:has-text('Continue to application'), button:has-text('Review')").first
                if next_btn.is_visible():
                    next_btn.click()
                    time.sleep(2)
                else:
                    break

            return False
        except Exception as e:
            print(f"  [-] Application step exception: {e}")
            return False