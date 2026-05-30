import re
import uuid
from typing import Any

import requests

from config import SupplierCredentials
from suppliers.browser_utils import extract_price
from suppliers.models import PartResult, SupplierSearchResult

BASE = "https://www.firstcallonline.com"
AUTH_BASE = f"{BASE}/FirstCallOnline"
SEARCH_BASE = f"{BASE}/FirstCallOnline/modernized/entsearch-search-service"
MARKET_ID = "06"
PLATFORM = "PLATFORM_05"


def _headers(token: str | None = None, sticky: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "X-Commit-Session": "true",
        "X-Request-ID": str(uuid.uuid4()),
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if sticky:
        headers["x-sticky"] = sticky
    return headers


def _login(session: requests.Session, creds: SupplierCredentials) -> tuple[str | None, str | None]:
    response = session.post(
        f"{AUTH_BASE}/auth/rest/v2/login",
        json={
            "loginName": creds.user,
            "password": creds.password,
            "rememberMe": True,
        },
        headers=_headers(),
        timeout=30,
    )

    if response.status_code != 200:
        try:
            payload = response.json()
            message = payload.get("message") or payload.get("errorId") or response.text[:160]
        except Exception:
            message = response.text[:160]
        raise RuntimeError(f"Login failed ({response.status_code}): {message}")

    data = response.json()
    token = data.get("access_token") or data.get("accessToken")
    sticky = response.headers.get("x-sticky") or session.cookies.get("stickySessionId")
    return token, sticky


def _get_store_info(session: requests.Session, token: str, sticky: str | None) -> tuple[int, str]:
    response = session.get(
        f"{AUTH_BASE}/session/user",
        headers=_headers(token, sticky),
        timeout=30,
    )
    store_id = 0
    platform = PLATFORM

    if response.status_code == 200:
        try:
            data = response.json()
            shop = data.get("currentShop") or {}
            home_store = shop.get("homeStore") or {}
            store_id = int(home_store.get("storeId") or shop.get("storeNumber") or 0)
            platform = shop.get("platform") or data.get("platform") or PLATFORM
        except Exception:
            pass

    return store_id, platform


def _collect_products(node: Any, query: str, found: list[dict]) -> None:
    if isinstance(node, dict):
        price = None
        for key, value in node.items():
            key_lower = key.lower()
            if key_lower in {"price", "yourprice", "listprice", "unitprice", "cost", "amount", "totalprice"}:
                if isinstance(value, (int, float)):
                    price = float(value)
                elif isinstance(value, str):
                    price = extract_price(value)
            if price is None and key_lower.endswith("price") and isinstance(value, (int, float)):
                price = float(value)

        brand = (
            node.get("brandName")
            or node.get("manufacturerName")
            or node.get("description")
            or node.get("partDescription")
            or node.get("title")
            or node.get("lineCode")
            or query
        )
        availability = (
            node.get("availabilityText")
            or node.get("availability")
            or node.get("storeAvailability")
            or "En tienda / In stock"
        )

        if price and price > 0:
            found.append(
                {
                    "brand": str(brand)[:80],
                    "price": price,
                    "eta": str(availability),
                }
            )

        for value in node.values():
            _collect_products(value, query, found)

    elif isinstance(node, list):
        for item in node:
            _collect_products(item, query, found)


def _search_parts(
    session: requests.Session,
    token: str,
    sticky: str | None,
    query: str,
    store_number: int,
    platform: str,
) -> list[dict]:
    headers = _headers(token, sticky)
    endpoints = [
        (
            f"{SEARCH_BASE}/v2/searches/pre-process/products",
            {
                "features": [{"type": "PART_TYPE_MATCHING"}],
                "productSearchRequest": {
                    "pageSize": 5,
                    "marketId": MARKET_ID,
                    "platform": platform,
                    "sessionId": "1",
                    "query": query,
                    "storeNumber": store_number,
                },
            },
        ),
        (
            f"{SEARCH_BASE}/v1/searches/item-number",
            {"marketId": MARKET_ID, "size": 5, "query": query},
        ),
        (
            f"{SEARCH_BASE}/v1/searches/products",
            {
                "features": [{"type": "FACET_MANUFACTURER_BRAND_NAMES_AND_CODES"}],
                "resultOffset": 0,
                "pageSize": 5,
                "marketId": MARKET_ID,
                "storeNumber": store_number,
                "sorts": [],
                "filters": [],
                "platform": platform,
                "sessionId": "1",
                "requestContext": {},
            },
        ),
    ]

    collected: list[dict] = []
    for url, body in endpoints:
        try:
            response = session.post(url, json=body, headers=headers, timeout=30)
            if response.status_code != 200:
                continue
            if "application/json" not in response.headers.get("Content-Type", ""):
                continue

            payload = response.json()
            _collect_products(payload, query, collected)
            if collected:
                break
        except Exception:
            continue

    deduped: list[dict] = []
    seen: set[tuple[str, float]] = set()
    for row in collected:
        key = (row["brand"].lower(), row["price"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped[:5]


def search_oreilly(
    creds: SupplierCredentials,
    query: str,
    vin: str | None = None,
) -> SupplierSearchResult:
    store = "O'Reilly First Call"
    if not creds.configured:
        return SupplierSearchResult(store=store, error="Missing O'Reilly credentials in .env")

    session = requests.Session()
    try:
        token, sticky = _login(session, creds)
        if not token:
            return SupplierSearchResult(store=store, error="O'Reilly login succeeded but no access token was returned")

        store_number, platform = _get_store_info(session, token, sticky)
        rows = _search_parts(session, token, sticky, query, store_number, platform)
        if not rows:
            return SupplierSearchResult(
                store=store,
                error="O'Reilly login worked but no priced results were found for that part",
            )

        parts = [
            PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"])
            for row in rows
        ]
        return SupplierSearchResult(store=store, parts=parts)
    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"O'Reilly error: {exc}")
    finally:
        session.close()
