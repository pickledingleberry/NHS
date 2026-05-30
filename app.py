import streamlit as st
import requests

from config import get_config
from suppliers.engine import search_all_suppliers
from db import init_db, save_quote, get_quotes
from jargon import map_jargon
from diagnostics import lookup_code

# Initialize SQLite database
init_db()

SUPPLIER_COLORS = {
    "AutoZone Pro": "#f97316",
    "O'Reilly First Call": "#16a34a",
    "Factory Motor Parts (FMP)": "#2563eb",
}

st.set_page_config(
    page_title="Taller del Barrio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Session defaults ---
if "lang" not in st.session_state:
    st.session_state.lang = "Español"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "quick_part" not in st.session_state:
    st.session_state.quick_part = ""
if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = []
if "supplier_errors" not in st.session_state:
    st.session_state.supplier_errors = []
if "hide_non_fitting" not in st.session_state:
    st.session_state.hide_non_fitting = True

TEXT = {
    "Español": {
        "shop_name": "Taller del Barrio",
        "shop_tagline": "Tu taller de confianza en el vecindario",
        "welcome": "¡Bienvenido!",
        "welcome_sub": "Aquí puede buscar refacciones y hacer una cotización en minutos. Todo es fácil — paso por paso.",
        "btn_start": "Empezar una Cotización",
        "btn_help": "Cómo Usar el Sistema",
        "btn_home": "Volver al Inicio",
        "card_quote_title": "Cotizar Refacciones",
        "card_quote_desc": "Ponga el VIN del carro, escriba la pieza que necesita, y le damos el precio total.",
        "card_help_title": "Ayuda Rápida",
        "card_help_desc": "Instrucciones sencillas para usar el sistema sin complicaciones.",
        "card_contact_title": "Contacto del Taller",
        "card_contact_desc": "Llámenos si tiene dudas. Estamos para servirle.",
        "phone": "Teléfono: (555) 123-4567",
        "hours": "Horario: Lun–Sáb 8:00 AM – 6:00 PM",
        "address": "123 Calle Principal, Su Ciudad",
        "step1": "Paso 1 — Carro",
        "step2": "Paso 2 — Pieza",
        "step3": "Paso 3 — Resultado",
        "vin_lbl": "Número VIN (17 letras y números)",
        "vin_hint": "El VIN está en el tablero del lado del conductor o en la puerta.",
        "vin_ok": "Carro encontrado:",
        "vin_bad": "VIN no válido. Revise que sean 17 caracteres.",
        "part_lbl": "¿Qué pieza necesita?",
        "part_hint": "Ejemplo: balatas, alternador, filtro de aceite",
        "part_ph": "Escriba aquí...",
        "toggle_cheap": "Mostrar solo la opción más barata",
        "labor_lbl": "Horas de mano de obra",
        "labor_hint": "Tarifa: $100 por hora",
        "btn_search": "Buscar Precios y Calcular Total",
        "searching": "Buscando en tiendas de refacciones...",
        "need_part": "Por favor escriba qué pieza necesita.",
        "env_missing": "Faltan credenciales en el archivo .env. Agregue sus usuarios y contraseñas de AutoZone, FMP y O'Reilly.",
        "no_results": "No se encontraron precios. Revise la pieza o las credenciales del proveedor.",
        "supplier_errors": "Avisos de proveedores:",
        "suppliers_ready": "Proveedores listos:",
        "cheapest": "¡LA MÁS BARATA!",
        "price": "Precio",
        "stock": "Disponible",
        "summary": "Resumen de su Cotización",
        "parts_line": "Refacciones (con margen del taller)",
        "labor_line": "Mano de obra",
        "total": "TOTAL ESTIMADO",
        "square_btn": "Cobrar con Square",
        "square_total": "Total para la terminal:",
        "tax_lbl": "Impuesto (%)",
        "discount_lbl": "Descuento",
        "discount_type_pct": "Porcentaje (%)",
        "discount_type_fixed": "Monto fijo ($)",
        "subtotal": "Subtotal",
        "tax_line": "Impuesto",
        "discount_line": "Descuento",
        "history_btn": "📋 Ver Historial",
        "save_btn": "💾 Guardar en Historial",
        "save_success": "✅ ¡Cotización guardada con éxito!",
        "cust_name_lbl": "Nombre del cliente",
        "obd_lbl": "Asistente OBD-II (Código de error, ej: P0302)",
        "obd_btn": "🔍 Analizar Código",
        "obd_causes": "Posibles causas:",
        "obd_suggested": "Refacciones sugeridas:",
        "search_history": "Buscar en historial (Nombre, VIN, Pieza)",
        "help_title": "Cómo Usar — Muy Fácil",
        "help_steps": [
            ("1.", "Entre el VIN de 17 dígitos del carro del cliente."),
            ("2.", "Escriba el nombre de la pieza (ej: balatas delanteras)."),
            ("3.", "Ponga las horas de trabajo si aplica."),
            ("4.", "Presione el botón azul grande para ver precios y el total."),
        ],
        "help_tip": "Consejo: Si no sabe el VIN, pídale al cliente que lo busque en su seguro o tarjeta de registro.",
        "lang_btn": "English",
        "footer": "Hecho con cariño para el taller de la familia",
        # Sidebar
        "sidebar_title": "⚙️ Configuración del Taller",
        "sidebar_labor": "Horas de mano de obra",
        "sidebar_tax": "Impuesto (%)",
        "sidebar_discount": "Descuento",
        "sidebar_discount_pct": "Porcentaje (%)",
        "sidebar_discount_fixed": "Monto fijo ($)",
        "sidebar_cheapest": "Solo opción más barata",
        "sidebar_fitment": "Solo piezas garantizadas",
        "sidebar_status": "Estado de Proveedores",
        "sidebar_connected": "Conectado",
        "sidebar_not_configured": "Sin configurar",
        # Results
        "top_recs_title": "Recomendaciones Principales",
        "quick_search_hint": "Buscar rápido:",
        "no_compat_parts": "No se encontraron piezas compatibles para este VIN.",
        "quoting_with": "Cotizando con:",
        "results_count": "resultado(s)",
        "brands_count": "marca(s)",
        "available_count": "disponible(s)",
        "labor_auto": "Estimado automático",
        # Badges
        "badge_fits": "Encaja",
        "badge_no_fit": "No encaja",
        "badge_in_store": "En Tienda",
        "badge_no_stock": "Sin stock",
        # ProVantage
        "pv_title": "ProVantage Auto Repair Network",
        "pv_sub": "Garantía Extendida Incluida — Válida en Todo el País",
        # Tier labels
        "tier_budget": "Económico / Budget",
        "tier_mid": "Intermedio / Mid",
        "tier_premium": "Premium",
        "tier_no_stock": "Sin stock",
        "tier_no_fit": "No encajan con este vehículo",
        "tier_other": "Otras opciones",
    },
    "English": {
        "shop_name": "Neighborhood Auto Shop",
        "shop_tagline": "Your trusted neighborhood repair shop",
        "welcome": "Welcome!",
        "welcome_sub": "Look up parts and build a quote in minutes. Easy step-by-step.",
        "btn_start": "Start a Quote",
        "btn_help": "How to Use",
        "btn_home": "Back to Home",
        "card_quote_title": "Get a Parts Quote",
        "card_quote_desc": "Enter the VIN, type the part you need, and we'll show the full estimate.",
        "card_help_title": "Quick Help",
        "card_help_desc": "Simple instructions — no tech skills needed.",
        "card_contact_title": "Shop Contact",
        "card_contact_desc": "Call us anytime you have questions.",
        "phone": "Phone: (555) 123-4567",
        "hours": "Hours: Mon–Sat 8:00 AM – 6:00 PM",
        "address": "123 Main Street, Your City",
        "step1": "Step 1 — Vehicle",
        "step2": "Step 2 — Part",
        "step3": "Step 3 — Results",
        "vin_lbl": "VIN Number (17 characters)",
        "vin_hint": "Found on the driver's dashboard or door sticker.",
        "vin_ok": "Vehicle found:",
        "vin_bad": "Invalid VIN. Please check all 17 characters.",
        "part_lbl": "What part do you need?",
        "part_hint": "Example: brake pads, alternator, oil filter",
        "part_ph": "Type here...",
        "toggle_cheap": "Show cheapest option only",
        "labor_lbl": "Labor hours",
        "labor_hint": "Rate: $100 per hour",
        "btn_search": "Find Prices & Calculate Total",
        "searching": "Searching parts stores...",
        "need_part": "Please enter a part name.",
        "env_missing": "Missing credentials in .env. Add your AutoZone, FMP, and O'Reilly logins.",
        "no_results": "No prices found. Check the part name or supplier credentials.",
        "supplier_errors": "Supplier notices:",
        "suppliers_ready": "Suppliers ready:",
        "cheapest": "CHEAPEST OPTION!",
        "price": "Price",
        "stock": "Availability",
        "summary": "Your Quote Summary",
        "parts_line": "Parts (with shop markup)",
        "labor_line": "Labor",
        "total": "ESTIMATED TOTAL",
        "square_btn": "Charge with Square",
        "square_total": "Terminal total:",
        "tax_lbl": "Tax (%)",
        "discount_lbl": "Discount",
        "discount_type_pct": "Percentage (%)",
        "discount_type_fixed": "Fixed amount ($)",
        "subtotal": "Subtotal",
        "tax_line": "Tax",
        "discount_line": "Discount",
        "history_btn": "📋 View History",
        "save_btn": "💾 Save to History",
        "save_success": "✅ Quote successfully saved!",
        "cust_name_lbl": "Customer name",
        "obd_lbl": "OBD-II Assistant (Error code, e.g. P0302)",
        "obd_btn": "🔍 Analyze Code",
        "obd_causes": "Possible causes:",
        "obd_suggested": "Suggested parts:",
        "search_history": "Search history (Name, VIN, Part)",
        "help_title": "How to Use — Very Easy",
        "help_steps": [
            ("1.", "Enter the customer's 17-digit VIN."),
            ("2.", "Type the part name (e.g. front brake pads)."),
            ("3.", "Set labor hours if needed."),
            ("4.", "Press the big blue button to see prices and total."),
        ],
        "help_tip": "Tip: If you don't have the VIN, ask the customer to check their insurance card or registration.",
        "lang_btn": "Español",
        "footer": "Built with love for the family shop",
        # Sidebar
        "sidebar_title": "⚙️ Shop Settings",
        "sidebar_labor": "Labor hours",
        "sidebar_tax": "Tax (%)",
        "sidebar_discount": "Discount",
        "sidebar_discount_pct": "Percentage (%)",
        "sidebar_discount_fixed": "Fixed amount ($)",
        "sidebar_cheapest": "Cheapest option only",
        "sidebar_fitment": "Verified-fit parts only",
        "sidebar_status": "Supplier Status",
        "sidebar_connected": "Connected",
        "sidebar_not_configured": "Not configured",
        # Results
        "top_recs_title": "Top Recommendations",
        "quick_search_hint": "Quick search:",
        "no_compat_parts": "No compatible parts found for this VIN.",
        "quoting_with": "Quoting with:",
        "results_count": "result(s)",
        "brands_count": "brand(s)",
        "available_count": "available",
        "labor_auto": "Auto estimate",
        # Badges
        "badge_fits": "Fits",
        "badge_no_fit": "Does not fit",
        "badge_in_store": "In Store",
        "badge_no_stock": "No stock",
        # ProVantage
        "pv_title": "ProVantage Auto Repair Network",
        "pv_sub": "Extended Nationwide Warranty Included",
        # Tier labels
        "tier_budget": "Budget",
        "tier_mid": "Mid",
        "tier_premium": "Premium",
        "tier_no_stock": "Out of stock",
        "tier_no_fit": "Does not fit this vehicle",
        "tier_other": "Other options",
    },
}

T = TEXT[st.session_state.lang]


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        /* ── Base ── */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 16px;
            background: #f1f5f9;
            color: #1e293b;
        }
        .block-container {
            padding-top: 0.75rem;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 100% !important;
        }

        /* ── Hero banner – clean navy ── */
        .hero {
            background: linear-gradient(120deg, #1e3a8a 0%, #1d4ed8 100%);
            border-radius: 16px;
            padding: 1.6rem 2rem;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px rgba(29,78,216,0.25);
        }
        .hero h1 { font-size: 2rem; font-weight: 800; margin: 0; color: white !important; }
        .hero p   { font-size: 1rem; margin: 0.3rem 0 0; color: #bfdbfe; }

        /* ── Welcome ── */
        .welcome-box {
            background: white;
            border: 2px solid #dbeafe;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .welcome-box h2 { color: #1e3a8a; font-size: 1.7rem; margin: 0 0 0.4rem; }
        .welcome-box p  { color: #475569; font-size: 1.05rem; margin: 0; }

        /* ── Info cards (homepage) ── */
        .info-card {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 14px;
            padding: 1.2rem;
            height: 100%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .info-card h3 { color: #1e3a8a; font-size: 1.1rem; margin: 0 0 0.4rem; }
        .info-card p  { color: #64748b; font-size: 0.95rem; margin: 0; line-height: 1.5; }

        /* ── Step badge ── */
        .step-badge {
            display: inline-block;
            background: #1e3a8a;
            color: white;
            font-weight: 700;
            font-size: 0.88rem;
            padding: 0.35rem 1rem;
            border-radius: 999px;
            margin-bottom: 0.75rem;
            letter-spacing: 0.2px;
        }

        /* ── Hint text ── */
        .hint { color: #94a3b8; font-size: 0.85rem; margin-top: -0.35rem; }

        /* ── Grand total box ── */
        .total-box {
            background: linear-gradient(135deg, #15803d, #16a34a);
            color: white;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            margin-top: 0.8rem;
            box-shadow: 0 4px 16px rgba(22,163,74,0.3);
        }
        .total-box .label { font-size: 0.78rem; color: #bbf7d0; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600; }
        .total-box .amount { font-size: 2.8rem; font-weight: 800; margin: 0.2rem 0; }

        /* ── Help steps ── */
        .help-step {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.6rem;
            font-size: 1rem;
            color: #1e293b;
        }

        /* ── Primary buttons – bold blue ── */
        div.stButton > button {
            font-size: 1rem !important;
            font-weight: 700 !important;
            padding: 0.65rem 1.25rem !important;
            border-radius: 10px !important;
            transition: all 0.15s ease;
            box-shadow: none !important;
        }
        div.stButton > button[kind="primary"] {
            background: #1d4ed8 !important;
            border: none !important;
            color: white !important;
            font-size: 1.05rem !important;
        }
        div.stButton > button[kind="primary"]:hover { background: #1e40af !important; }
        div[data-testid="column"] .stButton > button { min-height: 46px; }

        /* ── Sidebar – clean white ── */
        [data-testid="stSidebar"] {
            background: white !important;
            border-right: 2px solid #e2e8f0 !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #1e293b !important;
            font-size: 0.95rem !important;
        }

        /* ── Product result cards ── */
        .part-card {
            background: white;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            border: 2px solid #e2e8f0;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .part-card:hover {
            border-color: #93c5fd;
            box-shadow: 0 4px 14px rgba(29,78,216,0.08);
        }

        /* ── Quick-search buttons – smaller, pill style ── */
        div[data-testid="column"] .stButton > button[kind="secondary"] {
            background: white !important;
            border: 2px solid #e2e8f0 !important;
            color: #1e293b !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            padding: 0.4rem 0.6rem !important;
            border-radius: 10px !important;
        }
        div[data-testid="column"] .stButton > button[kind="secondary"]:hover {
            border-color: #1d4ed8 !important;
            color: #1d4ed8 !important;
        }

        .footer-text {
            text-align: center;
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-bottom: 1rem;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(config) -> dict:
    """Render the business settings sidebar and return the selected values."""
    with st.sidebar:
        st.markdown(f"## {T['sidebar_title']}")
        st.divider()

        # ── Supplier status badges ──────────────────────────────────────
        st.markdown(f"**{T['sidebar_status']}**")
        az_ok = config.autozone.configured
        or_ok = config.oreilly.configured
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div style="background:{"#f0fdf4" if az_ok else "#f8fafc"};border:2px solid {"#16a34a" if az_ok else "#e2e8f0"};border-radius:10px;padding:8px 10px;font-size:0.78em;color:{"#15803d" if az_ok else "#94a3b8"};font-weight:700;text-align:center;">🟠 AutoZone<br>{"✔ " + T["sidebar_connected"] if az_ok else T["sidebar_not_configured"]}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div style="background:{"#f0fdf4" if or_ok else "#f8fafc"};border:2px solid {"#16a34a" if or_ok else "#e2e8f0"};border-radius:10px;padding:8px 10px;font-size:0.78em;color:{"#15803d" if or_ok else "#94a3b8"};font-weight:700;text-align:center;">🟢 O\'Reilly<br>{"✔ " + T["sidebar_connected"] if or_ok else T["sidebar_not_configured"]}</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Labor ──────────────────────────────────────────────────────
        st.markdown(f"**{T['sidebar_labor']}**")
        st.caption(T["labor_hint"])
        labor_hours = st.number_input("labor_in", min_value=0.0, max_value=20.0, value=1.0, step=0.5, label_visibility="collapsed")

        st.divider()

        # ── Tax ────────────────────────────────────────────────────────
        st.markdown(f"**{T['sidebar_tax']}**")
        tax_rate = st.number_input("tax_in", min_value=0.0, max_value=25.0, value=0.0, step=0.25, format="%.2f", label_visibility="collapsed")

        st.divider()

        # ── Discount ────────────────────────────────────────────────────
        st.markdown(f"**{T['sidebar_discount']}**")
        discount_type = st.radio("disc_type", [T["sidebar_discount_pct"], T["sidebar_discount_fixed"]], horizontal=True, label_visibility="collapsed")
        discount_val = st.number_input("disc_val", min_value=0.0, max_value=10000.0, value=0.0, step=1.0, label_visibility="collapsed")

        st.divider()

        # ── Toggles ─────────────────────────────────────────────────────
        show_cheapest = st.toggle(T["sidebar_cheapest"], value=False)
        hide_non_fitting = st.toggle(T["sidebar_fitment"], value=st.session_state.hide_non_fitting)
        if hide_non_fitting != st.session_state.hide_non_fitting:
            st.session_state.hide_non_fitting = hide_non_fitting
            st.rerun()

    return {
        "labor_hours": labor_hours,
        "tax_rate": tax_rate,
        "discount_type": discount_type,
        "discount_val": discount_val,
        "show_cheapest": show_cheapest,
        "hide_non_fitting": hide_non_fitting,
    }


def render_toolbar():
    show_back = st.session_state.page != "home"
    col_back, col_hist, col_mid, col_lang = st.columns([1.2, 1.4, 3.2, 1.2])

    with col_back:
        if show_back:
            if st.button(T["btn_home"], use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

    with col_hist:
        if st.button(T["history_btn"], use_container_width=True):
            st.session_state.page = "history"
            st.rerun()

    with col_lang:
        if st.button(T["lang_btn"], use_container_width=True):
            st.session_state.lang = "English" if st.session_state.lang == "Español" else "Español"
            st.rerun()


def render_header():
    st.markdown(
        f"""
        <div class="hero">
            <h1>{T['shop_name']}</h1>
            <p>{T['shop_tagline']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home():
    st.markdown(
        f"""
        <div class="welcome-box">
            <h2>{T['welcome']}</h2>
            <p>{T['welcome_sub']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(T["btn_start"], type="primary", use_container_width=True):
        st.session_state.page = "quote"
        st.rerun()

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{T['card_quote_title']}</h3>
                <p>{T['card_quote_desc']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{T['card_help_title']}</h3>
                <p>{T['card_help_desc']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(T["btn_help"], use_container_width=True):
            st.session_state.page = "help"
            st.rerun()
    with c3:
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{T['card_contact_title']}</h3>
                <p>{T['card_contact_desc']}</p>
                <br>
                <p>{T['phone']}<br>{T['hours']}<br>{T['address']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def decode_vin(vin):
    if len(vin) < 17:
        return None
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    try:
        results = requests.get(url, timeout=10).json().get("Results", [])
        car = {"Year": "", "Make": "", "Model": "", "Engine": "", "Cylinders": "", "EngineL": 0.0}
        for item in results:
            var, val = item.get("Variable"), item.get("Value")
            if not val or val in ("Not Applicable", "null"):
                continue
            if var == "Model Year":
                car["Year"] = val
            elif var == "Make":
                car["Make"] = val
            elif var == "Model":
                car["Model"] = val
            elif var == "Displacement (L)":
                car["Engine"] = f"{val}L"
                try:
                    car["EngineL"] = float(val)
                except ValueError:
                    pass
            elif var == "Engine Number of Cylinders":
                car["Cylinders"] = val
        if car["Year"] and car["Make"]:
            return car
    except Exception:
        return None
    return None


def get_tech_specs(car: dict) -> dict:
    """Estimate common service specs from VIN decode data."""
    engine_l = car.get("EngineL", 0.0)
    year = int(car.get("Year") or 0)
    make = (car.get("Make") or "").title()

    # Oil capacity estimate by displacement
    if engine_l <= 1.6:
        oil_qt = "3.5–4.0"
    elif engine_l <= 2.0:
        oil_qt = "4.0–4.5"
    elif engine_l <= 2.5:
        oil_qt = "4.5–5.0"
    elif engine_l <= 3.5:
        oil_qt = "5.0–6.0"
    elif engine_l <= 5.0:
        oil_qt = "6.0–7.0"
    else:
        oil_qt = "7.0–8.0"

    # Oil viscosity by year
    if year >= 2015:
        oil_type = "0W-20" if engine_l <= 2.5 else "5W-20"
    elif year >= 2000:
        oil_type = "5W-30"
    else:
        oil_type = "10W-30"

    # Lug nut torque by make (approximate)
    torque_map = {
        "Toyota": "76–80 ft-lbs", "Lexus": "76–80 ft-lbs",
        "Honda": "80 ft-lbs", "Acura": "80–85 ft-lbs",
        "Nissan": "80–83 ft-lbs", "Infiniti": "80–95 ft-lbs",
        "Ford": "100–150 ft-lbs", "Lincoln": "100–150 ft-lbs",
        "Chevrolet": "100–140 ft-lbs", "Gmc": "100–140 ft-lbs",
        "Dodge": "95–130 ft-lbs", "Chrysler": "95–110 ft-lbs",
        "Jeep": "95–100 ft-lbs", "Ram": "130–135 ft-lbs",
        "Bmw": "88–103 ft-lbs", "Mercedes-Benz": "88–110 ft-lbs",
        "Audi": "89–96 ft-lbs", "Volkswagen": "88–96 ft-lbs",
        "Hyundai": "65–80 ft-lbs", "Kia": "65–80 ft-lbs",
        "Subaru": "89 ft-lbs", "Mazda": "80–88 ft-lbs",
        "Mitsubishi": "72–80 ft-lbs",
    }
    torque = torque_map.get(make, "80–100 ft-lbs")

    return {
        "oil_qty": f"{oil_qt} qts",
        "oil_type": oil_type,
        "torque": torque,
    }


# ---- Part category quick buttons ----
QUICK_PARTS = [
    ("🛑", "Balatas", "Brake Pads", "balatas"),
    ("💿", "Discos", "Rotors", "discos"),
    ("🔧", "Balatas + Discos", "Brake Kit", "brake kit"),
    ("🛢️", "Filtro de Aceite", "Oil Filter", "oil filter"),
    ("💨", "Filtro de Aire", "Air Filter", "air filter"),
    ("⚡", "Bujías", "Spark Plugs", "spark plugs"),
    ("🔋", "Batería", "Battery", "battery"),
    ("⚙️", "Alternador", "Alternator", "alternator"),
    ("🚗", "Marcha", "Starter", "starter"),
    ("🌡️", "Termostato", "Thermostat", "thermostat"),
    ("💧", "Bomba de Agua", "Water Pump", "water pump"),
    ("〰️", "Banda", "Belt", "serpentine belt"),
    ("📡", "Sensor O2", "O2 Sensor", "oxygen sensor"),
    ("🔩", "Amortiguadores", "Shocks/Struts", "shocks"),
    ("🔄", "Clutch", "Clutch", "clutch"),
    ("🔀", "Eje CV", "CV Axle", "cv axle"),
]


# ---- Labor estimation guide ----
LABOR_ESTIMATES = [
    (["brake pad", "balata", "freno"], 1.5, "Cambio de balatas / Brake pads replacement"),
    (["rotor", "disco"], 2.0, "Cambio de discos y balatas / Rotor & pads replacement"),
    (["spark plug", "bujia", "bujía"], 1.0, "Cambio de bujías / Spark plugs change"),
    (["oil filter", "filtro de aceite", "filtro aceite"], 0.5, "Servicio de aceite y filtro / Oil service"),
    (["air filter", "filtro de aire", "filtro aire"], 0.3, "Reemplazo de filtro de aire / Air filter change"),
    (["alternator", "alternador"], 2.0, "Reemplazo de alternador / Alternator swap"),
    (["starter", "marcha"], 1.5, "Reemplazo de marcha / Starter replacement"),
    (["battery", "batería", "bateria"], 0.5, "Cambio de batería / Battery change"),
    (["water pump", "bomba de agua"], 3.5, "Bomba de agua / Water pump swap"),
    (["thermostat", "termostato"], 1.5, "Termostato / Thermostat change"),
    (["serpentine belt", "banda", "correa"], 0.8, "Banda de accesorios / Serpentine belt change"),
    (["shocks", "amortiguador", "strut"], 3.0, "Amortiguadores (par) / Struts replacement (pair)"),
]


def estimate_labor_hours(query: str) -> float:
    q = query.lower()
    for keywords, hours, desc in LABOR_ESTIMATES:
        if any(k in q for k in keywords):
            return hours
    return 1.0  # default fallback


def render_quote():
    config = get_config()
    sidebar_vals = render_sidebar(config)
    labor_hours = sidebar_vals["labor_hours"]
    tax_rate = sidebar_vals["tax_rate"]
    discount_type = sidebar_vals["discount_type"]
    discount_val = sidebar_vals["discount_val"]
    show_cheapest = sidebar_vals["show_cheapest"]

    if not config.any_configured:
        st.warning(T["env_missing"])

    # ── Step 1: VIN + Customer Info ─────────────────────────────────────────
    vin_col, spec_col = st.columns([2, 1])
    with vin_col:
        st.markdown(f'<span class="step-badge">{T["step1"]}</span>', unsafe_allow_html=True)
        cust_name = st.text_input(T["cust_name_lbl"], placeholder="e.g. Juan Perez")
        vin_in = st.text_input(T["vin_lbl"], max_chars=17, placeholder="1HGBH41JXMN109186").upper()
        st.markdown(f'<p class="hint">{T["vin_hint"]}</p>', unsafe_allow_html=True)

    car_info = None
    if vin_in and len(vin_in) == 17:
        car_info = decode_vin(vin_in)
        with vin_col:
            if car_info:
                st.success(f"{T['vin_ok']} **{car_info['Year']} {car_info['Make']} {car_info['Model']}** {car_info['Engine']}")
            else:
                st.error(T["vin_bad"])

        # Tech specs card
        if car_info:
            specs = get_tech_specs(car_info)
            with spec_col:
                st.markdown(
                    f"""
                    <div style="background:#f0f9ff;border:2px solid #bae6fd;border-radius:12px;padding:14px 16px;margin-top:28px;">
                        <div style="font-weight:700;color:#0369a1;margin-bottom:8px;">Datos Técnicos / Tech Specs</div>
                        <table style="width:100%;font-size:0.88em;border-collapse:collapse;">
                            <tr><td style="color:#6b7280;padding:3px 0;">Aceite / Oil</td><td style="font-weight:600;text-align:right;">{specs['oil_type']}</td></tr>
                            <tr><td style="color:#6b7280;padding:3px 0;">Capacidad / Capacity</td><td style="font-weight:600;text-align:right;">{specs['oil_qty']}</td></tr>
                            <tr><td style="color:#6b7280;padding:3px 0;">Torque llantas / Lug nuts</td><td style="font-weight:600;text-align:right;">{specs['torque']}</td></tr>
                        </table>
                        <div style="font-size:0.72em;color:#94a3b8;margin-top:6px;">* Estimado — verify with shop manual</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── OBD-II Diagnostic Assistant (New!) ──────────────────────────────────
    st.write("")
    obd_col, info_col = st.columns([2, 1])
    with obd_col:
        obd_in = st.text_input(T["obd_lbl"], max_chars=5, placeholder="P0302").upper().strip()
        if obd_in:
            diag = lookup_code(obd_in)
            if diag:
                st.info(f"**OBD-II Code {obd_in}**: {diag['title']}\n\n{diag['desc']}")
                with info_col:
                    st.markdown(
                        f"""
                        <div style="background:#fff1f2;border:2px solid #fecdd3;border-radius:12px;padding:14px 16px;">
                            <div style="font-weight:700;color:#be123c;margin-bottom:6px;">{T['obd_causes']}</div>
                            <ul style="margin:0;padding-left:18px;font-size:0.88em;color:#9f1239;">
                                {"".join(f"<li>{c}</li>" for c in diag['causes'])}
                            </ul>
                            <div style="font-weight:700;color:#be123c;margin-top:10px;margin-bottom:4px;">{T['obd_suggested']}</div>
                            {"".join(f'<span style="background:#fda4af;color:#9f1239;padding:2px 8px;border-radius:4px;font-size:0.8em;margin-right:4px;display:inline-block;margin-bottom:4px;">{p}</span>' for p in diag['parts'])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                # Let user click any suggested diagnostic part to quick-search it
                st.markdown("<p style='color:#6b7280;font-size:0.85em;margin-bottom:2px;'>Sugerencia diagnóstica / Diagnostic click to search:</p>", unsafe_allow_html=True)
                sg_cols = st.columns(len(diag["parts"]) + 1)
                for s_idx, part_s in enumerate(diag["parts"]):
                    with sg_cols[s_idx]:
                        if st.button(f"🔍 {part_s.title()}", key=f"diag_{part_s}"):
                            st.session_state.quick_part = part_s
                            st.rerun()
            else:
                st.error("Código no encontrado / Diagnostic code not in database")

    # ── Step 2: Part Search + Quick Buttons ────────────────────────────────
    st.write("")
    st.markdown(f'<span class="step-badge">{T["step2"]}</span>', unsafe_allow_html=True)

    # Quick-category buttons — 4 per row, clean single-line labels
    st.markdown(f"<p style='color:#94a3b8;font-size:0.86em;margin-bottom:4px;'>{T['quick_search_hint']}</p>", unsafe_allow_html=True)
    rows = [QUICK_PARTS[i:i+4] for i in range(0, len(QUICK_PARTS), 4)]
    for row in rows:
        btn_cols = st.columns(len(row))
        for j, (icon, spa, eng, search_val) in enumerate(row):
            label = spa if st.session_state.lang == "Español" else eng
            with btn_cols[j]:
                if st.button(f"{icon} {label}", key=f"qbtn_{spa}", use_container_width=True):
                    st.session_state.quick_part = search_val
                    st.rerun()

    part_default = st.session_state.quick_part
    part_in = st.text_input(T["part_lbl"], value=part_default, placeholder=T["part_ph"])
    if part_in != part_default:
        st.session_state.quick_part = part_in
    st.markdown(f'<p class="hint">{T["part_hint"]}</p>', unsafe_allow_html=True)
    
    # Auto-update labor hours estimate in sidebar
    estimated_hours = estimate_labor_hours(part_in)
    if estimated_hours != labor_hours and part_in:
        st.caption(f"{T['labor_auto']}: **{estimated_hours} hrs** — {T['labor_hint']}")

    st.write("")
    if st.button(T["btn_search"], type="primary", use_container_width=True):
        if not part_in.strip():
            st.warning(T["need_part"])
        else:
            with st.spinner(T["searching"]):
                # Apply the Spanish-to-English jargon mapper!
                translated_query = map_jargon(part_in.strip())
                
                results, errors = search_all_suppliers(
                    translated_query,
                    vin=vin_in if len(vin_in) == 17 else None,
                    config=config,
                )
                st.session_state.scraped_data = results
                st.session_state.supplier_errors = errors
                st.session_state.selected_idx = 0
                st.rerun()

    # ── Display Results ──────────────────────────────────────────────────────
    scraped_data = st.session_state.scraped_data
    supplier_errors = st.session_state.supplier_errors

    if supplier_errors:
        with st.expander(T["supplier_errors"], expanded=False):
            for message in supplier_errors:
                st.write(f"- {message}")

    if scraped_data:
        # Filter out non-fitting if toggle is enabled (strictly show only verified fitting recommendations)
        if st.session_state.hide_non_fitting and vin_in and len(vin_in) == 17:
            scraped_data = [p for p in scraped_data if p.fits_vehicle and not p.does_not_fit]

        if not scraped_data:
            st.warning(T["no_compat_parts"])
        else:
            st.session_state.selected_idx = min(st.session_state.selected_idx, len(scraped_data) - 1)
            display_items = [scraped_data[0]] if show_cheapest else scraped_data

            st.markdown(f'<span class="step-badge">{T["step3"]}</span>', unsafe_allow_html=True)

            brand_count = len({p.brand for p in display_items})
            avail_count = sum(1 for p in display_items if p.available)
            st.caption(f"{len(display_items)} {T['results_count']} · {brand_count} {T['brands_count']} · {avail_count} {T['available_count']}")

            has_vin = bool(vin_in and len(vin_in) == 17 and car_info)

            # ── 1. Top 3 verified recommendations (Always visible) ─────────────────
            top_recs = [p for p in display_items if p.fits_vehicle and p.available][:3]
            other_items = [p for p in display_items if p not in top_recs]

            def _part_card(item, global_idx, key_prefix, scraped_data):
                """Render a clean, simple product card and return True if selected."""
                is_sel = global_idx == st.session_state.selected_idx
                bc = SUPPLIER_COLORS.get(item.store, "#475569")
                border = f"2px solid {bc}" if is_sel else "2px solid #e2e8f0"
                shadow = f"box-shadow:0 0 0 3px {bc}33,0 4px 14px rgba(0,0,0,0.06);" if is_sel else "box-shadow:0 2px 8px rgba(0,0,0,0.04);"

                # Badges row
                badges = f'<span style="background:{bc};color:white;padding:1px 7px;border-radius:5px;font-size:0.7em;font-weight:700;margin-right:4px;">{item.store}</span>'
                if item.fits_vehicle:
                    badges += f'<span style="background:#dcfce7;color:#15803d;padding:1px 7px;border-radius:5px;font-size:0.7em;font-weight:700;margin-right:4px;">{T["badge_fits"]}</span>'
                elif has_vin and not item.fits_vehicle:
                    badges += f'<span style="background:#fee2e2;color:#dc2626;padding:1px 7px;border-radius:5px;font-size:0.7em;font-weight:700;margin-right:4px;">{T["badge_no_fit"]}</span>'
                if item.store_qty > 0:
                    badges += f'<span style="background:#dbeafe;color:#1d4ed8;padding:1px 7px;border-radius:5px;font-size:0.7em;font-weight:700;margin-right:4px;">{T["badge_in_store"]}</span>'
                if not item.available:
                    badges += f'<span style="background:#f1f5f9;color:#94a3b8;padding:1px 7px;border-radius:5px;font-size:0.7em;">{T["badge_no_stock"]}</span>'

                # Position
                pos_html = ""
                _pc = {"Front": "#3b82f6", "Rear": "#7c3aed", "Front and Rear": "#0891b2"}
                for p in (item.position or "").split("/"):
                    p = p.strip()
                    if p:
                        pos_html += f'<span style="background:{_pc.get(p,"#64748b")};color:white;padding:1px 7px;border-radius:5px;font-size:0.7em;margin-right:3px;">{p}</span>'

                # Key specs only (1-2 most important)
                key_attrs = list((item.attributes or {}).items())[:2]
                specs_html = " &nbsp;·&nbsp; ".join(f'<span style="color:#64748b;font-size:0.78em;">{v}</span>' for k, v in key_attrs)

                list_html = f'<span style="color:#94a3b8;text-decoration:line-through;font-size:0.82em;margin-left:6px;">${item.list_price:.2f}</span>' if item.list_price > item.price else ""
                avail_html = ""
                if item.store_qty > 0:
                    avail_html = f'<span style="color:#16a34a;font-size:0.8em;font-weight:600;">{item.store_qty} {T["badge_in_store"]}</span>'
                elif item.total_qty > 0:
                    avail_html = f'<span style="color:#64748b;font-size:0.8em;">{item.eta}</span>'
                else:
                    avail_html = f'<span style="color:#ef4444;font-size:0.8em;">{T["badge_no_stock"]}</span>'

                img_html = f'<img src="{item.image_url}" style="width:68px;height:68px;object-fit:contain;border-radius:8px;border:1px solid #e2e8f0;margin-right:12px;flex-shrink:0;background:white;" onerror="this.style.display=\'none\'"/>' if item.image_url else ""
                pn_html = f'<span style="color:#94a3b8;font-size:0.75em;">#{item.part_number}</span>' if item.part_number else ""

                st.markdown(f"""
                    <div style="border:{border};border-radius:12px;background:white;padding:12px 14px;margin-bottom:8px;{shadow}opacity:{"0.45" if not item.available else "1"};">
                        <div style="display:flex;align-items:flex-start;">
                            {img_html}
                            <div style="flex:1;min-width:0;">
                                <div style="margin-bottom:5px;">{badges} {pos_html}</div>
                                <div style="font-size:0.97em;font-weight:700;color:#0f172a;line-height:1.3;margin-bottom:2px;">{item.brand} {item.description}</div>
                                <div style="margin-bottom:5px;">{pn_html} &nbsp; {specs_html}</div>
                                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px;">
                                    <div>
                                        <span style="font-size:1.5em;font-weight:800;color:{bc};">${item.price:.2f}</span>
                                        {list_html}
                                    </div>
                                    <div style="text-align:right;">{avail_html}</div>
                                </div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                if item.available:
                    lbl = "✅ Seleccionado" if is_sel else ("Usar para cotizar" if st.session_state.lang == "Español" else "Use for quote")
                    if st.button(lbl, key=f"{key_prefix}_{global_idx}", use_container_width=True,
                                 type="primary" if is_sel else "secondary"):
                        st.session_state.selected_idx = global_idx
                        st.rerun()

            if top_recs:
                st.markdown(f"<h4 style='color:#1e3a8a;margin-bottom:8px;'>⭐ {T['top_recs_title']}</h4>", unsafe_allow_html=True)
                for pair in [top_recs[i:i+3] for i in range(0, len(top_recs), 3)]:
                    gcols = st.columns(len(pair))
                    for col, item in zip(gcols, pair):
                        global_idx = next((i for i, p in enumerate(scraped_data) if p is item), 0)
                        with col:
                            _part_card(item, global_idx, "sel_top", scraped_data)

            # ── 2. Collapsible Price Tiers (All other options) ────────────────────
            avail_parts = [p for p in other_items if p.available and not p.does_not_fit]
            unavail_parts = [p for p in other_items if not p.available and not p.does_not_fit]
            wrong_fit_parts = [p for p in other_items if p.does_not_fit]

            def assign_tier(parts):
                if not parts:
                    return []
                if len(parts) < 4:
                    return [(f"🔧 {T['tier_other']}", parts)]
                prices = sorted(set(p.price for p in parts))
                low_cut = prices[len(prices) // 3]
                hi_cut = prices[2 * len(prices) // 3]
                budget = [p for p in parts if p.price <= low_cut]
                mid = [p for p in parts if low_cut < p.price <= hi_cut]
                prem = [p for p in parts if p.price > hi_cut]
                tiers = []
                if budget:
                    tiers.append((f"💚 {T['tier_budget']}  —  ${budget[0].price:.2f}–${budget[-1].price:.2f}", budget))
                if mid:
                    tiers.append((f"💛 {T['tier_mid']}  —  ${mid[0].price:.2f}–${mid[-1].price:.2f}", mid))
                if prem:
                    tiers.append((f"💎 {T['tier_premium']}  —  ${prem[0].price:.2f}–${prem[-1].price:.2f}", prem))
                return tiers

            tiers = assign_tier(avail_parts)
            if unavail_parts:
                tiers.append((f"⬇️ {T['tier_no_stock']}", unavail_parts))
            if wrong_fit_parts:
                tiers.append((f"❌ {T['tier_no_fit']}", wrong_fit_parts))

            for tier_label, tier_parts in tiers:
                is_collapsed = any(k in tier_label for k in (T["tier_no_stock"], T["tier_no_fit"]))
                with st.expander(tier_label, expanded=not is_collapsed):
                    for pair in [tier_parts[i:i+2] for i in range(0, len(tier_parts), 2)]:
                        gcols = st.columns(len(pair))
                        for col, item in zip(gcols, pair):
                            global_idx = next((i for i, p in enumerate(scraped_data) if p is item), 0)
                            with col:
                                _part_card(item, global_idx, "sel_tier", scraped_data)

            # ---- QUOTE TOTALS ----
            sel_idx = st.session_state.selected_idx
            if sel_idx >= len(scraped_data):
                sel_idx = 0
                st.session_state.selected_idx = 0
            chosen_part = scraped_data[sel_idx] if scraped_data else display_items[0]
            st.info(f"**{T['quoting_with']}** {chosen_part.brand} {chosen_part.description} — ${chosen_part.price:.2f} ({chosen_part.store})")
            chosen_part_cost = chosen_part.price
            parts_markup = chosen_part_cost * 1.30
            calculated_labor = labor_hours * 100.00
            subtotal = parts_markup + calculated_labor

            # Discount
            if discount_type == T["discount_type_pct"]:
                discount_amount = subtotal * (discount_val / 100.0)
            else:
                discount_amount = float(discount_val)
            after_discount = max(0.0, subtotal - discount_amount)

            # Tax
            tax_amount = after_discount * (tax_rate / 100.0)
            grand_total = after_discount + tax_amount

            # ProVantage badge
            st.markdown(
                f"""
                <div style="background:linear-gradient(120deg,#1e3a8a,#1d4ed8);border-radius:12px;padding:14px 18px;margin:18px 0 10px;display:flex;align-items:center;gap:14px;box-shadow:0 4px 16px rgba(29,78,216,0.2);">
                    <div style="font-size:2em;">🏆</div>
                    <div>
                        <div style="color:#fbbf24;font-weight:800;font-size:1em;">{T["pv_title"]}</div>
                        <div style="color:#bfdbfe;font-size:0.85em;">{T["pv_sub"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(f"### {T['summary']}")
            col_l, col_r = st.columns(2)
            with col_l:
                st.metric(T["parts_line"], f"${parts_markup:.2f}")
                st.metric(f"{T['labor_line']} ({labor_hours} hrs)", f"${calculated_labor:.2f}")
                if discount_amount > 0:
                    st.metric(f"- {T['discount_line']}", f"-${discount_amount:.2f}", delta_color="inverse")
                if tax_amount > 0:
                    st.metric(f"+ {T['tax_line']} ({tax_rate:.2f}%)", f"${tax_amount:.2f}")
            with col_r:
                st.markdown(
                    f"""
                    <div class="total-box">
                        <div class="label">{T['total']}</div>
                        <div class="amount">${grand_total:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{T['square_total']}** `${grand_total:.2f}`")
                st.button(T["square_btn"], key="pay_with_square_button", use_container_width=True)

                st.write("")
                # "Save to History" button action (New!)
                if st.button(T["save_btn"], type="secondary", use_container_width=True):
                    vehicle_desc = f"{car_info['Year']} {car_info['Make']} {car_info['Model']}" if car_info else "Vehículo Genérico"
                    save_quote(
                        customer_name=cust_name if cust_name else "Cliente General",
                        vin=vin_in,
                        vehicle_desc=vehicle_desc,
                        part_name=chosen_part.description,
                        part_brand=chosen_part.brand,
                        part_number=chosen_part.part_number,
                        part_cost=parts_markup,
                        labor_hours=labor_hours,
                        discount=discount_amount,
                        tax=tax_amount,
                        grand_total=grand_total,
                        store=chosen_part.store,
                    )
                    st.success(T["save_success"])


def render_history():
    if st.button(T["btn_home"]):
        st.session_state.page = "home"
        st.rerun()

    st.markdown("## 📋 Historial de Cotizaciones / Quote History")
    search_q = st.text_input(T["search_history"], placeholder="e.g. Juan Perez, 2011 Toyota, balatas")
    
    quotes_list = get_quotes(search_q)
    if not quotes_list:
        st.info("No se encontraron registros / No records found")
    else:
        for q in quotes_list:
            st.markdown(
                f"""
                <div style="background:white;border-radius:10px;padding:16px 20px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1e3a8a;">
                    <div style="display:flex;justify-content:between;align-items:baseline;margin-bottom:6px;flex-wrap:wrap;gap:8px;">
                        <span style="font-size:1.15em;font-weight:700;color:#1e3a8a;margin-right:12px;">👤 {q['customer_name']}</span>
                        <span style="color:#6b7280;font-size:0.85em;">📅 {q['created_at']}</span>
                    </div>
                    <div style="font-size:0.95em;color:#374151;margin-bottom:8px;">
                        🚗 Carro: <strong>{q['vehicle_desc']}</strong> &nbsp;|&nbsp; 
                        VIN: <code>{q['vin']}</code>
                    </div>
                    <div style="font-size:0.95em;color:#374151;margin-bottom:12px;">
                        🔧 Refacción: <strong>{q['part_brand']} {q['part_name']}</strong> &nbsp;|&nbsp;
                        Part #: <code>{q['part_number']}</code> ({q['store']})
                    </div>
                    <div style="display:flex;align-items:center;justify-content:space-between;border-top:1px solid #f3f4f6;padding-top:10px;flex-wrap:wrap;gap:10px;">
                        <div style="font-size:0.88em;color:#6b7280;">
                            Partes (+Markup): ${q['part_cost']:.2f} &nbsp;·&nbsp;
                            Mano de Obra ({q['labor_hours']} hrs): ${q['labor_hours']*100:.2f} &nbsp;·&nbsp;
                            Desc: -${q['discount']:.2f} &nbsp;·&nbsp;
                            Tax: +${q['tax']:.2f}
                        </div>
                        <div style="font-size:1.35em;font-weight:800;color:#10b981;">TOTAL: ${q['grand_total']:.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_help():
    st.markdown(f"## {T['help_title']}")
    for icon, step in T["help_steps"]:
        st.markdown(
            f'<div class="help-step">{icon} {step}</div>',
            unsafe_allow_html=True,
        )
    st.info(T["help_tip"])

    st.write("")
    if st.button(T["btn_start"], type="primary", use_container_width=True):
        st.session_state.page = "quote"
        st.rerun()


# --- Main ---
apply_styles()
render_toolbar()
render_header()

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "quote":
    render_quote()
elif st.session_state.page == "history":
    render_history()
else:
    render_help()

st.markdown(f'<p class="footer-text">{T["footer"]}</p>', unsafe_allow_html=True)
