import os
import os
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page


class BrowserManager:
    def __init__(self, user_data_dir: str = "./browser_profile", headless: bool = False):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.headless = headless
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.playwright = sync_playwright().start()
        
        # Launch persistent context to preserve manual LinkedIn login state
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Set a generous navigation timeout (60 seconds) to handle slow loads & verification pauses
        self.context.set_default_navigation_timeout(60000)
        self.context.set_default_timeout(30000)

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

    def stop(self):
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass