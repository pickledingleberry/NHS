from concurrent.futures import ThreadPoolExecutor, as_completed

from config import AppConfig, get_config
from suppliers.autozone import search_autozone
from suppliers.fmp import search_fmp
from suppliers.models import PartResult, SupplierSearchResult
from suppliers.oreilly import search_oreilly


def _best_part(result: SupplierSearchResult) -> PartResult | None:
    if not result.parts:
        return None
    return min(result.parts, key=lambda part: part.price)


def search_all_suppliers(
    query: str,
    vin: str | None = None,
    config: AppConfig | None = None,
) -> tuple[list[PartResult], list[str]]:
    config = config or get_config()
    jobs = []

    if config.autozone.configured:
        jobs.append(("autozone", search_autozone, config.autozone))
    if config.fmp.configured:
        jobs.append(("fmp", search_fmp, config.fmp))
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
            best = _best_part(supplier_result)
            if best:
                results.append(best)
            elif supplier_result.error:
                errors.append(f"{supplier_result.store}: {supplier_result.error}")

    results.sort(key=lambda item: item.price)
    return results, errors
