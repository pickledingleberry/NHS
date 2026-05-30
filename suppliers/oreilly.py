import re
import uuid
from typing import Any

import requests

from config import SupplierCredentials
from suppliers.models import PartResult, SupplierSearchResult

BASE = "https://www.oreillypro.com"
AUTH_URL = f"{BASE}/FirstCallOnline/auth/rest/v2/login"
SESSION_URL = f"{BASE}/FirstCallOnline/session/user"
VIN_LOOKUP_URL = f"{BASE}/FirstCallOnline/modernized/api/v1/vehicles/lookup"
PREPROCESS_URL = f"{BASE}/FirstCallOnline/modernized/entsearch-search-service/v2/searches/pre-process/products"
ENTERPRISE_URL = f"{BASE}/FirstCallOnline/parttype/mini/v2/enterprise/products"

PLATFORM_ID = "05"
MARKET_ID = "06"

# Common O'Reilly part type IDs (partTypeId format: 5-digit zero-padded string)
PART_TYPE_MAP = [
    (["brake pad", "balata", "freno", "disc pad"], "03351"),
    (["brake rotor", "rotor", "disco de freno", "disco"], "00896"),
    (["brake caliper", "caliper", "calibrador"], "00854"),
    (["oil filter", "filtro de aceite", "filtro aceite"], "00614"),
    (["air filter", "filtro de aire", "filtro aire"], "00049"),
    (["spark plug", "bujia", "bujía"], "01014"),
    (["alternator", "alternador"], "00065"),
    (["battery", "batería", "bateria"], "00099"),
    (["starter", "marcha", "motor de arranque"], "01035"),
    (["serpentine belt", "correa", "banda"], "00160"),
    (["wiper blade", "pluma", "limpiador"], "01116"),
    (["water pump", "bomba de agua"], "01095"),
    (["thermostat", "termostato"], "01055"),
    (["fuel filter", "filtro de combustible"], "00506"),
    (["cv axle", "cv shaft", "flecha", "axle"], "00226"),
    (["shock", "amortiguador"], "01009"),
    (["strut", "puntal"], "01042"),
    (["tie rod", "barra de dirección"], "01057"),
    (["wheel bearing", "balero", "rodamiento"], "00098"),
    (["oxygen sensor", "sensor de oxígeno", "o2 sensor"], "00642"),
    (["mass air flow", "maf sensor", "sensor maf"], "00578"),
    (["throttle body", "cuerpo de aceleración"], "01056"),
    (["brake drum", "tambor"], "00855"),
    (["brake shoe", "zapatas"], "00860"),
    (["clutch", "embrague", "clutch disc"], "00233"),
]


def _map_query_to_part_type_id(query: str) -> list[str]:
    q = query.lower()
    for keywords, pt_id in PART_TYPE_MAP:
        if any(k in q for k in keywords):
            return [pt_id]
    return []


def _headers(token: str | None = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "X-Commit-Session": "true",
        "X-Request-ID": str(uuid.uuid4()),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _login(session: requests.Session, creds: SupplierCredentials) -> str | None:
    r = session.post(
        AUTH_URL,
        json={"loginName": creds.user, "password": creds.password, "rememberMe": True},
        headers=_headers(),
        timeout=30,
    )
    if r.status_code != 200:
        try:
            msg = r.json().get("message") or r.json().get("errorId") or r.text[:120]
        except Exception:
            msg = r.text[:120]
        raise RuntimeError(f"Login failed ({r.status_code}): {msg}")
    data = r.json()
    return data.get("access_token") or data.get("accessToken")


def _get_shop_id(session: requests.Session, token: str) -> int:
    r = session.get(SESSION_URL, headers=_headers(token), timeout=20)
    if r.status_code != 200 or "application/json" not in r.headers.get("Content-Type", ""):
        return 0
    data = r.json()
    shop = data.get("currentShop") or {}
    return int(shop.get("id") or shop.get("shopId") or shop.get("storeNumber") or 0)


def _lookup_vehicle(session: requests.Session, token: str, vin: str) -> dict:
    r = session.get(
        VIN_LOOKUP_URL,
        params={"vin": vin},
        headers=_headers(token),
        timeout=20,
    )
    if r.status_code != 200 or "application/json" not in r.headers.get("Content-Type", ""):
        return {}
    data = r.json()
    vehicles = data if isinstance(data, list) else (data.get("vehicles") or [])
    return vehicles[0] if vehicles else {}


def _get_part_type_ids_from_api(session: requests.Session, token: str, query: str, store_number: int) -> list[str]:
    """Use pre-process search to find partTypeIds for a query."""
    body = {
        "features": [{"type": "PART_TYPE_MATCHING"}],
        "productSearchRequest": {
            "pageSize": 5,
            "marketId": MARKET_ID,
            "platform": f"PLATFORM_{PLATFORM_ID}",
            "sessionId": "1",
            "query": query,
            "storeNumber": store_number,
        },
    }
    try:
        r = session.post(PREPROCESS_URL, json=body, headers=_headers(token), timeout=20)
        if r.status_code != 200 or "application/json" not in r.headers.get("Content-Type", ""):
            return []
        ids: list[str] = []
        _collect_part_type_ids(r.json(), ids)
        return ids[:3]
    except Exception:
        return []


def _collect_part_type_ids(node: Any, ids: list[str]) -> None:
    if isinstance(node, dict):
        pt = node.get("partTypeId")
        if pt and str(pt) not in ids:
            ids.append(str(pt))
        for v in node.values():
            if isinstance(v, (dict, list)):
                _collect_part_type_ids(v, ids)
    elif isinstance(node, list):
        for item in node:
            _collect_part_type_ids(item, ids)


def _search_enterprise_products(
    session: requests.Session,
    token: str,
    vehicle: dict,
    shop_id: int,
    part_type_id: str,
) -> list[dict]:
    """Call O'Reilly enterprise/products endpoint for a given vehicle + partTypeId."""
    vehicle_block: dict = {
        "vehicleId": vehicle.get("vehicleId") or vehicle.get("id") or 0,
        "vin": vehicle.get("vin", ""),
        "year": vehicle.get("year", 0),
        "make": vehicle.get("make", ""),
        "model": vehicle.get("model", ""),
        "shopVehicleDescriptor": vehicle.get("shopVehicleDescriptor") or f"{vehicle.get('year','')} {vehicle.get('make','')} {vehicle.get('model','')}".strip(),
        "answeredAttributes": vehicle.get("answeredAttributes") or [],
        "showAllAttributes": [],
        "shopCustomerId": None,
    }
    if vehicle.get("id") and vehicle.get("id") != vehicle.get("vehicleId"):
        vehicle_block["id"] = vehicle.get("id")

    body = {
        "vehicle": vehicle_block,
        "platformId": PLATFORM_ID,
        "pageOffset": 0,
        "shopId": shop_id,
        "sort": {"resultFieldType": "SCORE", "sortOrder": "ASCENDING"},
        "partTypeId": part_type_id.zfill(5),
    }

    try:
        r = session.post(ENTERPRISE_URL, json=body, headers=_headers(token), timeout=30)
        if r.status_code != 200 or "application/json" not in r.headers.get("Content-Type", ""):
            return []
        data = r.json()
        return _parse_enterprise_products(data)
    except Exception:
        return []


def _parse_enterprise_products(data: dict) -> list[dict]:
    results: list[dict] = []
    products = data.get("products") or []
    for item in products:
        if not isinstance(item, dict):
            continue
        ppar = item.get("partPriceAvailabilityResponse") or {}
        price_block = ppar.get("price") or {}
        cost = price_block.get("itemCost")
        list_price = price_block.get("listPrice")
        price = float(cost) if isinstance(cost, (int, float)) and cost > 0 else None
        if not price and isinstance(list_price, (int, float)) and list_price > 0:
            price = float(list_price)
        if not price:
            continue

        product = item.get("product") or {}
        brand = product.get("brandName") or product.get("manufacturerName") or item.get("displayName", "")
        if not brand:
            brand = (item.get("itemDescription") or "")[:60]

        # Availability from partAvailabilityList
        avail_list = ppar.get("partAvailabilityList") or []
        if any(a.get("locationType") == "STORE" and a.get("quantityOnHand", 0) > 0 for a in avail_list):
            eta = "En tienda / In stock"
        elif any(a.get("locationType") == "HUB" and a.get("quantityOnHand", 0) > 0 for a in avail_list):
            eta = "Hub — 1 hr"
        elif avail_list:
            eta = "Entrega / Delivery"
        else:
            eta = "Disponible / Available"

        results.append({"brand": str(brand)[:80], "price": price, "eta": eta})

    return results


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

    session = requests.Session()
    try:
        token = _login(session, creds)
        if not token:
            return SupplierSearchResult(store=store, error="O'Reilly login succeeded but no token returned")

        shop_id = _get_shop_id(session, token)
        vehicle = _lookup_vehicle(session, token, vin)

        # Get part type IDs: try hardcoded mapping first, then API
        part_type_ids = _map_query_to_part_type_id(query)
        if not part_type_ids:
            part_type_ids = _get_part_type_ids_from_api(session, token, query, 0)
        if not part_type_ids:
            return SupplierSearchResult(
                store=store,
                error=f"O'Reilly: could not map '{query}' to a part type — try a more specific part name",
            )

        all_rows: list[dict] = []
        for pt_id in part_type_ids:
            rows = _search_enterprise_products(session, token, vehicle, shop_id, pt_id)
            all_rows.extend(rows)
            if len(all_rows) >= 5:
                break

        if not all_rows:
            return SupplierSearchResult(
                store=store,
                error="O'Reilly logged in but no priced results found for that part",
            )

        all_rows.sort(key=lambda x: x["price"])
        seen: set[tuple[str, float]] = set()
        parts: list[PartResult] = []
        for row in all_rows:
            key = (row["brand"].lower(), row["price"])
            if key in seen:
                continue
            seen.add(key)
            parts.append(PartResult(store=store, brand=row["brand"], price=row["price"], eta=row["eta"]))
            if len(parts) >= 5:
                break

        return SupplierSearchResult(store=store, parts=parts)

    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"O'Reilly error: {exc}")
    finally:
        session.close()
