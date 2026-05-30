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

LOGIN_URL = "https://www.autozonepro.com/ui/login"


def search_autozone(
    creds: SupplierCredentials,
    query: str,
    vin: str | None = None,
) -> SupplierSearchResult:
    store = "AutoZone Pro"
    if not creds.configured:
        return SupplierSearchResult(store=store, error="Missing AutoZone credentials in .env")

    try:
        with browser_page(engine="firefox") as page:
            safe_goto(page, LOGIN_URL)
            dismiss_overlays(page)

            # Step 1: Username
            if not wait_for_any(page, ['input[name="username"]', 'input[type="text"]'], timeout_ms=10000):
                return SupplierSearchResult(store=store, error="AutoZone login page did not load")

            if not fill_first(page, ['input[name="username"]', 'input[type="text"]'], creds.user):
                return SupplierSearchResult(store=store, error="Could not find AutoZone username field")

            page.locator('button[type="submit"]').first.click(force=True)
            page.wait_for_timeout(3000)

            # Step 2: Password on second screen
            if not wait_for_any(page, ['input[type="password"]', 'input[name="password"]'], timeout_ms=10000):
                return SupplierSearchResult(store=store, error="AutoZone password step did not appear — check username")

            for selector in ['input[type="radio"][value*="password" i]', 'label:has-text("Enter my password")']:
                try:
                    el = page.locator(selector).first
                    if el.count() and el.is_visible():
                        el.click(timeout=3000)
                        page.wait_for_timeout(500)
                        break
                except Exception:
                    pass

            if not fill_first(page, ['input[type="password"]', 'input[name="password"]'], creds.password):
                return SupplierSearchResult(store=store, error="Could not find AutoZone password field")

            page.locator('button[type="submit"]').first.click(force=True)
            page.wait_for_timeout(4000)

            if "login" in page.url.lower():
                return SupplierSearchResult(store=store, error="AutoZone login failed — check AZ_USER / AZ_PASS")

            # Step 3: VIN lookup if provided
            if vin and len(vin) == 17:
                try:
                    vin_selectors = [
                        'input[placeholder*="VIN"]',
                        'input[placeholder*="vin"]',
                        'input[aria-label*="VIN"]',
                    ]
                    if fill_first(page, vin_selectors, vin):
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(2000)
                except Exception:
                    pass

            # Step 4: Search for part
            # AutoZone Pro search bar placeholder: "Enter a product, keyword, part #, VIN, or license plate and state"
            search_selectors = [
                'input[placeholder*="product, keyword"]',
                'input[placeholder*="keyword"]',
                'input[placeholder*="part #"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'input[type="search"]',
                'input[name*="search"]',
                'input[class*="search"]',
            ]
            if not fill_first(page, search_selectors, query):
                return SupplierSearchResult(store=store, error="Could not find AutoZone search box after login")

            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)

            # Step 5: Scrape results
            cards = page.locator(
                '[data-testid*="product"], [class*="product-card"], '
                '[class*="ProductCard"], [class*="part-result"], '
                'article, [class*="search-result"]'
            )
            parsed: list[dict] = []
            for i in range(min(cards.count(), 12)):
                try:
                    text = cards.nth(i).inner_text(timeout=2000)
                except Exception:
                    continue
                if len(text) < 8:
                    continue
                price = extract_price(text)
                if price is None:
                    continue
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                brand = lines[0][:80] if lines else query
                eta = "En tienda / In stock"
                if any(w in text.lower() for w in ("tomorrow", "mañana", "next day")):
                    eta = "Mañana / Tomorrow"
                parsed.append({"brand": brand, "price": price, "eta": eta})

            if not parsed:
                # Last resort: look for any price on the page
                all_text = page.content()
                import re
                prices = re.findall(r'\$\s*([\d,]+\.\d{2})', all_text)
                prices = [float(p.replace(",", "")) for p in prices if 0.5 < float(p.replace(",", "")) < 9999]
                if prices:
                    parsed.append({"brand": query, "price": min(prices), "eta": "En tienda / In stock"})

            parts = [
                PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"])
                for row in unique_parts(parsed)
            ]
            if not parts:
                return SupplierSearchResult(store=store, error="AutoZone logged in but no priced results found")
            return SupplierSearchResult(store=store, parts=parts)

    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"AutoZone error: {exc}")
