import json
import re
import urllib.parse

from config import AutoZoneConfig, SupplierCredentials
from suppliers.browser_utils import (
    browser_page,
    dismiss_overlays,
    fill_first,
    safe_goto,
    wait_for_any,
)
from suppliers.models import PartResult, SupplierSearchResult

LOGIN_URL = "https://www.autozonepro.com/ui/login"
BASE = "https://www.autozonepro.com"


def _az_login(page) -> tuple[dict, bool]:
    """Perform two-step AutoZone login. Returns (session_data, success)."""
    safe_goto(page, LOGIN_URL)
    dismiss_overlays(page)

    if not wait_for_any(page, ['input[name="username"]', 'input[type="text"]'], timeout_ms=10000):
        return {}, False
    if not fill_first(page, ['input[name="username"]', 'input[type="text"]'], ""):
        return {}, False

    # This is a two-step login — username first, then password
    return {}, True


def _az_two_step_login(page, user: str, password: str) -> bool:
    safe_goto(page, LOGIN_URL)
    dismiss_overlays(page)

    if not wait_for_any(page, ['input[name="username"]', 'input[type="text"]'], timeout_ms=10000):
        return False

    if not fill_first(page, ['input[name="username"]', 'input[type="text"]'], user):
        return False

    page.locator('button[type="submit"]').first.click(force=True)
    page.wait_for_timeout(3000)

    if not wait_for_any(page, ['input[type="password"]'], timeout_ms=10000):
        return False

    for selector in ['input[type="radio"][value*="password" i]', 'label:has-text("Enter my password")']:
        try:
            el = page.locator(selector).first
            if el.count() and el.is_visible():
                el.click(timeout=3000)
                page.wait_for_timeout(500)
                break
        except Exception:
            pass

    if not fill_first(page, ['input[type="password"]', 'input[name="password"]'], password):
        return False

    page.locator('button[type="submit"]').first.click(force=True)
    page.wait_for_timeout(4000)
    return "login" not in page.url.lower()


def _get_session(page) -> dict:
    """Extract storeId and customerId from the logged-in page using multiple strategies."""
    data = page.evaluate("""
        () => {
            const results = {storeId: "", customerId: ""};

            // Strategy 1: Next.js __NEXT_DATA__
            const nd = window.__NEXT_DATA__;
            if (nd) {
                const str = JSON.stringify(nd.props || {});
                const cm = str.match(/"customerId":"?(\\d{4,})"?/);
                const sm = str.match(/"(?:storeId|primaryStoreId|homeStoreId)":"?(\\d{3,})"?/);
                if (cm) results.customerId = cm[1];
                if (sm) results.storeId = sm[1];
            }

            // Strategy 2: Scan all script tags for embedded JSON
            if (!results.customerId || !results.storeId) {
                document.querySelectorAll("script").forEach(s => {
                    const text = s.textContent || "";
                    if (text.includes("customerId") || text.includes("storeId")) {
                        const cm2 = text.match(/"customerId":"?(\\d{4,})"?/);
                        const sm2 = text.match(/"(?:storeId|primaryStoreId)":"?(\\d{3,})"?/);
                        if (cm2 && !results.customerId) results.customerId = cm2[1];
                        if (sm2 && !results.storeId) results.storeId = sm2[1];
                    }
                });
            }

            return results;
        }
    """)
    return data or {}


def _get_vehicle_data(page, vin: str) -> dict:
    """Get AutoZone vehicle IDs (makeId, modelId, vehicleQuestions) for a VIN."""
    result = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch(
                    '/sls/commercial/vehicle-service/vehicle/decoder/v1/parts-vehicle-questions-answers?vin={vin}',
                    {{credentials: 'include'}}
                );
                if (!r.ok) return {{}};
                return await r.json();
            }} catch(e) {{ return {{_error: e.message}}; }}
        }}
    """)
    return result or {}


def _search_part_groups(page, query: str, session: dict) -> list[str]:
    """Search and return partGroupIds for a query term."""
    body = {
        "searchText": query,
        "primaryStore": True,
        "includePnA": True,
        "interChange": False,
        "ignoreVehicleSpecificProductsCheck": True,
        "pageNumber": 1,
        "recordsPerPage": 5,
        "exactMatch": False,
    }
    if session.get("customerId"):
        body["customerId"] = session["customerId"]
    if session.get("storeId"):
        body["storeId"] = session["storeId"]

    result = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch('/sls/commercial-catalog/catalog/lookup/v4/search', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    credentials: 'include',
                    body: JSON.stringify({json.dumps(body)})
                }});
                return await r.json();
            }} catch(e) {{ return {{_error: e.message}}; }}
        }}
    """)

    if not result or "_error" in result:
        return []

    # Parse partGroupIds from redirectUrl: "?partGroupIds=azpg4204!azpg1368!..."
    redirect = result.get("redirectUrl", "")
    if "partGroupIds=" in redirect:
        raw = redirect.split("partGroupIds=")[1].split("&")[0]
        return raw.split("!")[:3]  # first 3 part groups
    return []


def _get_products(page, part_group_id: str, session: dict, vehicle: dict) -> list[dict]:
    """Fetch products for a partGroupId, return list of {brand, price, eta}."""
    params: dict = {
        "partGroupId": part_group_id,
        "ignoreVehicleSpecificProductsCheck": "false",
        "ignorePositionPreselection": "true",  # skip Front/Rear prompt
        "recordsPerPage": "5",
        "pageNumber": "1",
        "primaryStore": "true",
        "includePnA": "true",
    }

    if session.get("storeId"):
        params["storeId"] = session["storeId"]
    if session.get("customerId"):
        params["customerId"] = session["customerId"]

    # Add vehicle parameters if available
    make_id = vehicle.get("makeId") or vehicle.get("make", {}).get("makeId")
    model_id = vehicle.get("modelId") or vehicle.get("model", {}).get("modelId")
    year = vehicle.get("year")
    vehicle_type_id = vehicle.get("vehicleTypeId", "5")
    vehicle_questions = vehicle.get("vehicleQuestions") or _build_vehicle_questions(vehicle)

    if make_id and model_id and year:
        params.update({
            "makeId": str(make_id),
            "modelId": str(model_id),
            "year": str(year),
            "vehicleTypeId": str(vehicle_type_id),
        })
        if vehicle_questions:
            params["vehicleQuestions"] = vehicle_questions
    else:
        params["ignoreVehicleSpecificProductsCheck"] = "true"

    qs = urllib.parse.urlencode(params)
    result = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch('/sls/commercial-catalog/catalog/lookup/v3/products?{qs}',
                    {{credentials: 'include'}}
                );
                return await r.json();
            }} catch(e) {{ return {{_error: e.message}}; }}
        }}
    """)

    if not result or "_error" in result:
        return []

    parsed: list[dict] = []
    for sku in result.get("skuRecords", []):
        pna = sku.get("pna") or {}
        price = _extract_price_from_pna(pna)
        if not price:
            continue

        brand = sku.get("brandName") or ""
        description = sku.get("itemDescription") or sku.get("partGroupName") or ""
        part_number = sku.get("partNumber") or ""
        pricing = (pna.get("pricing") or {}).get("unformatted") or {}
        list_price = float(pricing.get("list") or 0)

        avail = pna.get("availability") or {}
        store_qty = int(avail.get("storeQuantity") or 0)
        total_qty = int(avail.get("combinedQuantity") or 0)
        if store_qty > 0:
            eta = "En tienda / In stock"
        elif avail.get("hubQuantity", 0) > 0 or avail.get("vdpQuantity", 0) > 0:
            eta = avail.get("deliveryDayAfterCutoff") or "Entrega hoy / Delivery today"
        elif avail.get("dmQuantity", 0) > 0:
            eta = "Mañana / Tomorrow"
        else:
            eta = "Disponible / Available"

        # Product attributes (Position, Pad Type, Hardware Included, etc.)
        attrs: dict = {}
        position = ""
        for attr in sku.get("productAttributes") or []:
            label = attr.get("label") or ""
            value = attr.get("value") or ""
            if label and value:
                attrs[label] = value
                if label.lower() == "location":
                    position = value

        fits = (sku.get("vehicleFitment") or {}).get("vehicleFit") == "FITS"

        parsed.append({
            "brand": brand[:80],
            "description": description[:100],
            "part_number": part_number,
            "price": price,
            "list_price": list_price,
            "eta": eta,
            "store_qty": store_qty,
            "total_qty": total_qty,
            "position": position,
            "attributes": attrs,
            "fits_vehicle": fits,
        })

    return parsed


def _extract_price_from_pna(pna: dict) -> float | None:
    """Extract shop cost from pna.pricing.unformatted.cost (AutoZone API structure)."""
    if not pna:
        return None
    # Primary path: pna.pricing.unformatted.cost
    pricing = pna.get("pricing") or {}
    unformatted = pricing.get("unformatted") or {}
    cost = unformatted.get("cost")
    if isinstance(cost, (int, float)) and cost > 0:
        return float(cost)
    # Fallback: list price
    list_price = unformatted.get("list")
    if isinstance(list_price, (int, float)) and list_price > 0:
        return float(list_price)
    # Fallback: formatted strings
    formatted = pricing.get("formatted") or {}
    for key in ("cost", "list"):
        val = formatted.get(key, "")
        if isinstance(val, str) and val.startswith("$"):
            try:
                v = float(val.replace("$", "").replace(",", ""))
                if v > 0:
                    return v
            except ValueError:
                pass
    return None


def _build_vehicle_questions(vehicle: dict) -> str:
    """Build vehicleQuestions string from whatever vehicle data is available."""
    answers = vehicle.get("answers") or vehicle.get("vehicleAnswers") or {}
    if isinstance(answers, dict):
        return "||".join(f"{k}:{v}" for k, v in answers.items())
    return ""


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
            if not _az_two_step_login(page, creds.user, creds.password):
                return SupplierSearchResult(store=store, error="AutoZone login failed — check AZ_USER / AZ_PASS")

            session = _get_session(page)

            # Prefer hardcoded values from .env over auto-detected ones
            az_cfg = creds if isinstance(creds, AutoZoneConfig) else None
            if az_cfg and az_cfg.store_id:
                session["storeId"] = az_cfg.store_id
            if az_cfg and az_cfg.customer_id:
                session["customerId"] = az_cfg.customer_id

            # If still missing, try fetching from account endpoint
            if not session.get("customerId") or not session.get("storeId"):
                try:
                    account_data = page.evaluate("""
                        async () => {
                            try {
                                const r = await fetch('/sls/commercial-catalog/catalog/lookup/v2/products/frequently-ordered',
                                    {credentials: 'include'});
                                return await r.json();
                            } catch(e) { return {}; }
                        }
                    """)
                    if account_data and account_data.get("customerId"):
                        session["customerId"] = str(account_data["customerId"])
                except Exception:
                    pass

            vehicle: dict = {}
            if vin and len(vin) == 17:
                vehicle = _get_vehicle_data(page, vin)

            part_group_ids = _search_part_groups(page, query, session)

            if not part_group_ids:
                part_group_ids = _fallback_part_groups(query)

            all_parts: list[dict] = []
            for pgid in part_group_ids:
                results = _get_products(page, pgid, session, vehicle)
                all_parts.extend(results)
                if len(all_parts) >= 5:
                    break

            if not all_parts:
                sid = session.get("storeId", "none")
                cid = session.get("customerId", "none")
                return SupplierSearchResult(
                    store=store,
                    error=(
                        f"AutoZone: no prices returned (storeId={sid}, customerId={cid}). "
                        "Add AZ_STORE_ID and AZ_CUSTOMER_ID to your .env file."
                    ),
                )

            # Sort by price, dedupe
            seen: set[tuple[str, float]] = set()
            parts: list[PartResult] = []
            for row in sorted(all_parts, key=lambda x: x["price"]):
                key = (row["brand"].lower(), row["price"])
                if key in seen:
                    continue
                seen.add(key)
                parts.append(PartResult(
                store=store,
                brand=row["brand"],
                description=row.get("description", ""),
                part_number=row.get("part_number", ""),
                price=row["price"],
                list_price=row.get("list_price", 0.0),
                eta=row["eta"],
                store_qty=row.get("store_qty", 0),
                total_qty=row.get("total_qty", 0),
                position=row.get("position", ""),
                attributes=row.get("attributes", {}),
                fits_vehicle=row.get("fits_vehicle", False),
            ))
                if len(parts) >= 5:
                    break

            return SupplierSearchResult(store=store, parts=parts)

    except Exception as exc:
        return SupplierSearchResult(store=store, error=f"AutoZone error: {exc}")


def _fallback_part_groups(query: str) -> list[str]:
    """Map common part names to AutoZone partGroupIds when API search fails."""
    q = query.lower()
    mapping = [
        (["brake pad", "balata", "freno delantero", "front brake"], ["azpg4204"]),
        (["rotor", "disco", "brake rotor"], ["azpg1368"]),
        (["brake kit", "brake set", "kit frenos"], ["60407"]),
        (["oil filter", "filtro aceite", "filtro de aceite"], ["azpg1294"]),
        (["air filter", "filtro aire", "filtro de aire"], ["azpg1296"]),
        (["spark plug", "bujia", "bujía"], ["azpg1302"]),
        (["alternator", "alternador"], ["azpg1356"]),
        (["battery", "batería", "bateria"], ["azpg1246"]),
        (["starter", "marcha", "arranque"], ["azpg1360"]),
        (["belt", "correa", "banda"], ["azpg1338"]),
        (["wiper", "limpiador", "pluma"], ["azpg1400"]),
    ]
    for keywords, ids in mapping:
        if any(k in q for k in keywords):
            return ids
    return []
