import re
from contextlib import contextmanager

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

DEFAULT_TIMEOUT_MS = 45000


@contextmanager
def browser_page(headless: bool = True):
    playwright: Playwright = sync_playwright().start()
    browser: Browser = playwright.chromium.launch(headless=headless)
    page: Page = browser.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    try:
        yield page
    finally:
        browser.close()
        playwright.stop()


def fill_first(page: Page, selectors: list[str], value: str) -> bool:
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue
        locator.first.fill(value)
        return True
    return False


def click_first(page: Page, selectors: list[str]) -> bool:
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue
        locator.first.click()
        return True
    return False


def wait_for_any(page: Page, selectors: list[str], timeout_ms: int = 15000) -> bool:
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False


def extract_price(text: str) -> float | None:
    match = re.search(r"\$\s*([\d,]+\.\d{2})", text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def unique_parts(rows: list[dict]) -> list[dict]:
    seen: set[tuple[str, float]] = set()
    unique: list[dict] = []
    for row in rows:
        key = (row.get("brand", "").lower(), row.get("price", 0.0))
        if key in seen or row.get("price", 0) <= 0:
            continue
        seen.add(key)
        unique.append(row)
    return unique[:5]
