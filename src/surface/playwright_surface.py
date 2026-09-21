from playwright.sync_api import sync_playwright
from .base import SurfaceAdapter


class PlaywrightSurface(SurfaceAdapter):

    def __init__(self, headless=False):
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=headless
        )

        self.page = self.browser.new_page()


    def navigate(self, url: str):
        self.page.goto(url)


    def fill(self, selector: str, value: str):
        self.page.locator(selector).fill(value)


    def click(self, selector: str):
        self.page.locator(selector).click()


    def read_text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text()


    def screenshot(self, path: str):
        self.page.screenshot(
            path=path,
            full_page=True
        )


    def close(self):
        self.browser.close()
        self.playwright.stop()