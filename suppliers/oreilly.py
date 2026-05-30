import re

from config import SupplierCredentials
from suppliers.browser_utils import (
    browser_page,
    dismiss_overlays,
    extract_price,
    fill_first,
    safe_goto,
    unique_parts,
    wait_for_any,
)
from suppliers.models import PartResult, SupplierSearchResult

LOGIN_URL = "https://www.oreillypro.com/login"


def search_oreilly(
    creds: SupplierCredentials,
    query: str,
    vin: str | None = None,
) -> SupplierSearchResult:
    store = "O'Reilly First Call"
    if not creds.configured:
        return SupplierSearchResult(store=store, error="Missing O'Reilly credentials in .env")
    if not vin or len(vin) < 17:
        return SupplierSearchResult(
            store=store,
            error="O'Reilly requires a VIN — enter the 17-digit VIN above before searching",
        )

    try:
        with browser_page(engine="firefox") as page:
            safe_goto(page, LOGIN_URL)
            page.wait_for_timeout(2000)
            dismiss_overlays(page)

            # Login
            if not wait_for_any(
                page,
                ["#loginName", 'input[name="loginName"]', 'input[placeholder="Username"]'],
                timeout_ms=10000,
            ):
                return SupplierSearchResult(store=store, error="O'Reilly login page did not load")

            if not fill_first(
                page,
                ["#loginName", 'input[name="loginName"]', 'input[placeholder="Username"]', 'input[type="text"]'],
                creds.user,
            ):
                return SupplierSearchResult(store=store, error="Could not find O'Reilly username field")

            if not fill_first(
                page,
                ['input[name="password"]', 'input[type="password"]', 'input[placeholder="Password"]'],
                creds.password,
            ):
                return SupplierSearchResult(store=store, error="Could not find O'Reilly password field")

            page.locator('button[type="submit"]').first.click(force=True)
            page.wait_for_timeout(5000)

            if "login" in page.url.lower():
                return SupplierSearchResult(store=store, error="O'Reilly login failed — check OR_USER / OR_PASS")

            dismiss_overlays(page)

            # Enter VIN to select vehicle
            vin_selectors = [
                'input[placeholder*="VIN"]',
                'input[aria-label*="VIN"]',
                'input[id*="vin" i]',
                'input[name*="vin" i]',
            ]
            if fill_first(page, vin_selectors, vin):
                try:
                    for selector in ['button:has-text("Go")', 'button[aria-label*="VIN"]', 'button[type="submit"]']:
                        btn = page.locator(selector).first
                        if btn.count() and btn.is_visible():
                            btn.click(timeout=4000)
                            break
                except Exception:
                    page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

            # Search for the part
            search_selectors = [
                'input[placeholder*="Product, Part"]',
                'input[placeholder*="Part #"]',
                'input[placeholder*="Brand"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'input[type="search"]',
            ]
            if not fill_first(page, search_selectors, query):
                return SupplierSearchResult(store=store, error="Could not find O'Reilly search box after login")

            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)

            # If O'Reilly asks "Front / Rear / Don't know", pick "Don't know or show all"
            for selector in [
                'a:has-text("Don\'t know")',
                'button:has-text("Don\'t know")',
                'a:has-text("show all")',
                'a:has-text("Show all")',
            ]:
                try:
                    el = page.locator(selector).first
                    if el.count() and el.is_visible():
                        el.click(timeout=3000)
                        page.wait_for_timeout(3000)
                        break
                except Exception:
                    pass

            # Scrape prices from product cards
            card_selectors = [
                '[class*="product-card"]',
                '[class*="ProductCard"]',
                '[data-testid*="product"]',
                '[class*="part-row"]',
                '[class*="search-result"]',
                'article',
                'li[class*="product"]',
                'tr[class*="product"]',
            ]
            parsed: list[dict] = []
            for selector in card_selectors:
                cards = page.locator(selector)
                if cards.count() == 0:
                    continue
                for i in range(min(cards.count(), 15)):
                    try:
                        text = cards.nth(i).inner_text(timeout=2000)
                    except Exception:
                        continue
                    if len(text) < 5:
                        continue
                    price = extract_price(text)
                    if price is None or price <= 0:
                        continue
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    brand = lines[0][:80] if lines else query
                    eta = "En tienda / In stock"
                    if any(w in text.lower() for w in ("tomorrow", "next day", "mañana")):
                        eta = "Mañana / Tomorrow"
                    parsed.append({"brand": brand, "price": price, "eta": eta})
                if parsed:
                    break

            if not parsed:
                # Last resort: scrape all dollar amounts from the page
                all_prices = re.findall(r'\$\s*([\d,]+\.\d{2})', page.content())
                valid = [float(p.replace(",", "")) for p in all_prices if 0.5 < float(p.replace(",", "")) < 9999]
                if valid:
                    parsed.append({"brand": query, "price": min(valid), "eta": "En tienda / In stock"})

            parts = [
                PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"])
                for row in unique_parts(parsed)
            ]
            if not parts:
                return SupplierSearchResult(
                    store=store,
                    error="O'Reilly logged in but no priced results found — try a specific part number",
                )
            return SupplierSearchResult(store=store, parts=parts)

    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"O'Reilly error: {exc}")
