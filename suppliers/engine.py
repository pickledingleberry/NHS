from concurrent.futures import ThreadPoolExecutor, as_completed

from config import AppConfig, get_config
from suppliers.autozone import search_autozone
from suppliers.fmp import search_fmp
from suppliers.models import PartResult, SupplierSearchResult
from suppliers.oreilly import search_oreilly


def search_all_suppliers(
    query: str,
    vin: str | None = None,
    config: AppConfig | None = None,
) -> tuple[list[PartResult], list[str]]:
    config = config or get_config()
    jobs = []

    if config.autozone.configured:
        jobs.append(("autozone", search_autozone, config.autozone))
    # if config.fmp.configured:
    #     jobs.append(("fmp", search_fmp, config.fmp))
    if config.oreilly.configured:
        jobs.append(("oreilly", search_oreilly, config.oreilly))

    if not jobs:
        return [], ["No supplier logins found in .env — add AZ_, FMP_, and OR_ credentials."]

    results: list[PartResult] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        future_map = {
            pool.submit(fn, creds, query, vin): name for name, fn, creds in jobs
        }
        for future in as_completed(future_map):
            supplier_result: SupplierSearchResult = future.result()
            if supplier_result.parts:
                results.extend(supplier_result.parts)
            if supplier_result.error:
                errors.append(f"{supplier_result.store}: {supplier_result.error}")

    # Brand-diverse sort: interleave brands so variety shows up before
    # showing multiple options from the same brand
    results = _brand_diverse_sort(results)
    return results, errors


def _brand_diverse_sort(parts: list[PartResult]) -> list[PartResult]:
    """Interleave brands so the list shows variety instead of one brand repeated.
    Within each brand, sort cheapest first. Brands ordered by their cheapest option."""
    by_brand: dict[str, list[PartResult]] = {}
    for p in parts:
        key = p.brand or "Other"
        by_brand.setdefault(key, []).append(p)

    for brand in by_brand:
        by_brand[brand].sort(key=lambda x: (x.price, 0 if x.store_qty > 0 else 1))

    brands_ordered = sorted(by_brand.keys(), key=lambda b: by_brand[b][0].price)
    max_len = max(len(v) for v in by_brand.values()) if by_brand else 0

    diverse: list[PartResult] = []
    for i in range(max_len):
        for brand in brands_ordered:
            if i < len(by_brand[brand]):
                diverse.append(by_brand[brand][i])
    return diverse
