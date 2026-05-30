from config import SupplierCredentials
from suppliers.browser_utils import (
    browser_page,
    click_first,
    extract_price,
    fill_first,
    unique_parts,
    wait_for_any,
)
from suppliers.models import PartResult, SupplierSearchResult


def search_autozone(
    creds: SupplierCredentials,
    query: str,
    vin: str | None = None,
) -> SupplierSearchResult:
    store = "AutoZone Pro"
    if not creds.configured:
        return SupplierSearchResult(store=store, error="Missing AutoZone credentials in .env")

    try:
        with browser_page() as page:
            page.goto("https://www.autozonepro.com/ui/login", wait_until="domcontentloaded")
            if not fill_first(
                page,
                ['input[name="username"]', 'input[id*="username"]', 'input[type="text"]'],
                creds.user,
            ):
                return SupplierSearchResult(store=store, error="Could not find AutoZone username field")

            if not fill_first(
                page,
                ['input[name="password"]', 'input[id*="password"]', 'input[type="password"]'],
                creds.password,
            ):
                return SupplierSearchResult(store=store, error="Could not find AutoZone password field")

            click_first(
                page,
                [
                    'button:has-text("Continue")',
                    'button:has-text("Sign In")',
                    'button[type="submit"]',
                ],
            )
            page.wait_for_timeout(4000)

            if "login" in page.url.lower():
                return SupplierSearchResult(store=store, error="AutoZone login failed — check AZ_USER / AZ_PASS")

            search_selectors = [
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'input[type="search"]',
                'input[name*="search"]',
            ]
            if not fill_first(page, search_selectors, query):
                return SupplierSearchResult(store=store, error="Could not find AutoZone search box")

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            cards = page.locator(
                '[data-testid*="product"], [class*="product"], [class*="part"], article, li'
            )
            parsed: list[dict] = []
            for i in range(min(cards.count(), 12)):
                text = cards.nth(i).inner_text(timeout=2000)
                if len(text) < 8:
                    continue
                price = extract_price(text)
                if price is None:
                    continue
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                brand = lines[0][:80] if lines else query
                eta = "En tienda / In stock"
                if any(word in text.lower() for word in ("tomorrow", "mañana", "next day")):
                    eta = "Mañana / Tomorrow"
                parsed.append({"brand": brand, "price": price, "eta": eta})

            parts = [
                PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"])
                for row in unique_parts(parsed)
            ]
            if not parts:
                return SupplierSearchResult(
                    store=store,
                    error="AutoZone logged in but no priced results were found for that part",
                )
            return SupplierSearchResult(store=store, parts=parts)
    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"AutoZone error: {exc}")
