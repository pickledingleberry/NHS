import re
from contextlib import contextmanager

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

DEFAULT_TIMEOUT_MS = 25000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

CHROMIUM_ARGS = [
    "--disable-http2",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--blink-settings=imagesEnabled=false",  # Speed up: don't load images
]


@contextmanager
def browser_page(headless: bool = True, engine: str = "chromium"):
    playwright: Playwright = sync_playwright().start()
    launch_kwargs = {"headless": headless}
    if engine == "chromium":
        launch_kwargs["args"] = CHROMIUM_ARGS
        browser: Browser = playwright.chromium.launch(**launch_kwargs)
    elif engine == "firefox":
        browser = playwright.firefox.launch(headless=headless)
    else:
        browser = playwright.chromium.launch(headless=headless, args=CHROMIUM_ARGS)

    context: BrowserContext = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        ignore_https_errors=True,
    )
    # block unnecessary scripts to save time and bandwidth
    context.route(
        "**/*.{png,jpg,jpeg,gif,webp,svg,mp4,webm,woff,woff2,ttf,eot}",
        lambda route: route.abort(),
    )
    context.route(
        re.compile(r"google-analytics|doubleclick|analytics|gtm|newrelic|hotjar", re.I),
        lambda route: route.abort(),
    )

    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    page: Page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    try:
        yield page
    finally:
        context.close()
        browser.close()
        playwright.stop()


def safe_goto(page: Page, url: str) -> None:
    last_error: Exception | None = None
    for wait_until in ("commit", "domcontentloaded"):
        try:
            page.goto(url, wait_until=wait_until, timeout=20000)
            return
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error


def dismiss_overlays(page: Page) -> None:
    page.evaluate(
        """
        () => {
            for (const selector of [
                '#onetrust-consent-sdk',
                '.onetrust-pc-dark-filter',
                '#onetrust-banner-sdk',
                '.cookie-consent',
                '#cookie-banner',
            ]) {
                document.querySelectorAll(selector).forEach((node) => node.remove());
            }
        }
        """
    )


def fill_first(page: Page, selectors: list[str], value: str) -> bool:
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue
        try:
            field = locator.first
            field.click(timeout=3000)
            field.fill(value)
            return True
        except Exception:
            continue
    return False


def click_first(page: Page, selectors: list[str], force: bool = False) -> bool:
    dismiss_overlays(page)
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue
        for use_force in (force, True) if not force else (True,):
            try:
                locator.first.click(timeout=4000, force=use_force)
                return True
            except Exception:
                continue
    return False


def submit_login(page: Page, button_selectors: list[str]) -> bool:
    dismiss_overlays(page)
    if click_first(page, button_selectors):
        return True
    try:
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False


def wait_for_any(page: Page, selectors: list[str], timeout_ms: int = 10000) -> bool:
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
