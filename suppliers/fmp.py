from config import SupplierCredentials
from suppliers.browser_utils import (
    browser_page,
    click_first,
    extract_price,
    fill_first,
    unique_parts,
)
from suppliers.models import PartResult, SupplierSearchResult


def search_fmp(
    creds: SupplierCredentials,
    query: str,
    vin: str | None = None,
) -> SupplierSearchResult:
    store = "Factory Motor Parts (FMP)"
    if not creds.configured:
        return SupplierSearchResult(store=store, error="Missing FMP credentials in .env")

    try:
        with browser_page() as page:
            page.goto("https://fmp-delivers.dstcloud.com/#/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            if not fill_first(
                page,
                [
                    'input[formcontrolname="userID"]',
                    'input[name="userID"]',
                    'input[placeholder*="User"]',
                    'input[type="text"]',
                ],
                creds.user,
            ):
                return SupplierSearchResult(store=store, error="Could not find FMP user field")

            if not fill_first(
                page,
                [
                    'input[formcontrolname="password"]',
                    'input[name="password"]',
                    'input[type="password"]',
                ],
                creds.password,
            ):
                return SupplierSearchResult(store=store, error="Could not find FMP password field")

            click_first(
                page,
                [
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    'button[type="submit"]',
                ],
            )
            page.wait_for_timeout(5000)

            if "login" in page.url.lower():
                return SupplierSearchResult(store=store, error="FMP login failed — check FMP_USER / FMP_PASS")

            search_selectors = [
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'input[type="search"]',
                'input[id*="search"]',
            ]
            if not fill_first(page, search_selectors, query):
                return SupplierSearchResult(store=store, error="Could not find FMP search box")

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            rows = page.locator("tr, [class*='result'], [class*='part'], li, article")
            parsed: list[dict] = []
            for i in range(min(rows.count(), 15)):
                text = rows.nth(i).inner_text(timeout=2000)
                if len(text) < 8:
                    continue
                price = extract_price(text)
                if price is None:
                    continue
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                brand = lines[0][:80] if lines else query
                eta = "20 min"
                if "will call" in text.lower() or "pickup" in text.lower():
                    eta = "Recoger / Will call"
                parsed.append({"brand": brand, "price": price, "eta": eta})

            parts = [
                PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"])
                for row in unique_parts(parsed)
            ]
            if not parts:
                return SupplierSearchResult(
                    store=store,
                    error="FMP logged in but no priced results were found for that part",
                )
            return SupplierSearchResult(store=store, parts=parts)
    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"FMP error: {exc}")
