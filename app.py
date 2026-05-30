import streamlit as st
import requests

from config import get_config
from suppliers.engine import search_all_suppliers

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
    },
}

T = TEXT[st.session_state.lang]


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
            font-size: 18px;
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 960px;
        }

        .hero {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
            border-radius: 20px;
            padding: 2.5rem 2rem;
            text-align: center;
            color: white;
            margin: 0 0 1.5rem 0;
            box-shadow: 0 8px 24px rgba(30, 58, 138, 0.25);
            width: 100%;
        }
        .hero h1 {
            font-size: 2.6rem;
            font-weight: 800;
            margin: 0;
            color: white !important;
        }
        .hero p {
            font-size: 1.25rem;
            margin: 0.5rem 0 0;
            opacity: 0.95;
        }

        .welcome-box {
            background: #fffbeb;
            border: 2px solid #fcd34d;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .welcome-box h2 {
            color: #92400e;
            font-size: 1.8rem;
            margin: 0 0 0.5rem;
        }
        .welcome-box p {
            color: #78350f;
            font-size: 1.15rem;
            margin: 0;
        }

        .info-card {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 16px;
            padding: 1.25rem;
            height: 100%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .info-card h3 {
            color: #1e3a8a;
            font-size: 1.35rem;
            margin: 0 0 0.5rem;
        }
        .info-card p {
            color: #4b5563;
            font-size: 1.05rem;
            margin: 0;
            line-height: 1.5;
        }

        .step-badge {
            display: inline-block;
            background: #1e3a8a;
            color: white;
            font-weight: 700;
            font-size: 1.1rem;
            padding: 0.4rem 1rem;
            border-radius: 999px;
            margin-bottom: 0.75rem;
        }

        .hint {
            color: #6b7280;
            font-size: 0.95rem;
            margin-top: -0.5rem;
        }

        .total-box {
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            margin-top: 1rem;
        }
        .total-box .label {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        .total-box .amount {
            font-size: 2.8rem;
            font-weight: 800;
            margin: 0.25rem 0;
        }

        .part-result {
            background: #f0f9ff;
            border-left: 5px solid #2563eb;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            font-size: 1.05rem;
        }
        .part-result.best {
            background: #ecfdf5;
            border-left-color: #059669;
        }

        .help-step {
            background: #f9fafb;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            font-size: 1.1rem;
            line-height: 1.5;
        }

        div.stButton > button {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 12px !important;
        }

        div.stButton > button[kind="primary"] {
            background: #2563eb !important;
            border: none !important;
        }

        div[data-testid="column"] .stButton > button {
            min-height: 48px;
        }

        .toolbar-spacer {
            height: 0.25rem;
        }

        .footer-text {
            text-align: center;
            color: #9ca3af;
            font-size: 0.95rem;
            margin-top: 2rem;
            padding-bottom: 1rem;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_toolbar():
    show_back = st.session_state.page != "home"
    col_back, col_mid, col_lang = st.columns([1.2, 4, 1.2])

    with col_back:
        if show_back:
            if st.button(T["btn_home"], use_container_width=True):
                st.session_state.page = "home"
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
        car = {"Year": "", "Make": "", "Model": "", "Engine": ""}
        for item in results:
            var, val = item.get("Variable"), item.get("Value")
            if var == "Model Year":
                car["Year"] = val
            elif var == "Make":
                car["Make"] = val
            elif var == "Model":
                car["Model"] = val
            elif var == "Displacement (L)":
                car["Engine"] = f"{val}L" if val else ""
        if car["Year"] and car["Make"]:
            return car
    except Exception:
        return None
    return None


def render_quote():
    config = get_config()
    if config.any_configured:
        st.caption(f"{T['suppliers_ready']} {' · '.join(config.status_lines())}")
    else:
        st.warning(T["env_missing"])

    st.markdown(f'<span class="step-badge">{T["step1"]}</span>', unsafe_allow_html=True)
    vin_in = st.text_input(T["vin_lbl"], max_chars=17, placeholder="1HGBH41JXMN109186").upper()
    st.markdown(f'<p class="hint">{T["vin_hint"]}</p>', unsafe_allow_html=True)

    car_info = None
    if vin_in and len(vin_in) == 17:
        car_info = decode_vin(vin_in)
        if car_info:
            st.success(
                f"{T['vin_ok']} **{car_info['Year']} {car_info['Make']} {car_info['Model']}** {car_info['Engine']}"
            )
        else:
            st.error(T["vin_bad"])

    st.write("")
    st.markdown(f'<span class="step-badge">{T["step2"]}</span>', unsafe_allow_html=True)
    part_in = st.text_input(T["part_lbl"], placeholder=T["part_ph"])
    st.markdown(f'<p class="hint">{T["part_hint"]}</p>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        show_cheapest = st.toggle(T["toggle_cheap"], value=False)
        labor_hours = st.number_input(T["labor_lbl"], min_value=0.0, max_value=20.0, value=1.0, step=0.5)
        st.caption(T["labor_hint"])
    with col_b:
        tax_rate = st.number_input(T["tax_lbl"], min_value=0.0, max_value=25.0, value=0.0, step=0.25, format="%.2f")
        discount_type = st.radio(T["discount_lbl"], [T["discount_type_pct"], T["discount_type_fixed"]], horizontal=True)
        discount_val = st.number_input("", min_value=0.0, max_value=10000.0, value=0.0, step=1.0, label_visibility="collapsed")

    st.write("")
    if st.button(T["btn_search"], type="primary", use_container_width=True):
        if not part_in.strip():
            st.warning(T["need_part"])
        else:
            with st.spinner(T["searching"]):
                scraped_data, supplier_errors = search_all_suppliers(
                    part_in.strip(),
                    vin=vin_in if len(vin_in) == 17 else None,
                    config=config,
                )

                if supplier_errors:
                    with st.expander(T["supplier_errors"], expanded=not scraped_data):
                        for message in supplier_errors:
                            st.write(f"- {message}")

                if not scraped_data:
                    st.error(T["no_results"])
                else:
                    display_items = [scraped_data[0]] if show_cheapest else scraped_data

                    st.markdown(f'<span class="step-badge">{T["step3"]}</span>', unsafe_allow_html=True)

                    if show_cheapest:
                        st.markdown(f"### {T['cheapest']}")

                    st.caption(f"{len(display_items)} resultado(s) / results — ordenado por precio / sorted by price")

                    for item in display_items:
                        is_best = item.price == scraped_data[0].price
                        supplier_colors = {
                            "AutoZone Pro": "#f97316",
                            "O'Reilly First Call": "#16a34a",
                            "Factory Motor Parts (FMP)": "#2563eb",
                        }
                        border_color = supplier_colors.get(item.store, "#6b7280")

                        badge_html = f'<span style="background:{border_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.78em;font-weight:700;margin-right:6px;">{item.store}</span>'
                        if item.fits_vehicle:
                            badge_html += '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:4px;font-size:0.78em;margin-right:4px;">Fits Vehicle</span>'
                        if item.store_qty > 0:
                            badge_html += '<span style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:4px;font-size:0.78em;margin-right:4px;">En Tienda</span>'
                        if is_best and not show_cheapest:
                            badge_html += '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:0.78em;">Mejor precio</span>'

                        pos_html = ""
                        for pos in (item.position or "").split("/"):
                            pos = pos.strip()
                            if pos:
                                pos_color = {"Front": "#3b82f6", "Rear": "#8b5cf6", "Front and Rear": "#0891b2"}.get(pos, "#6b7280")
                                pos_html += f'<span style="background:{pos_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;margin-right:4px;">{pos}</span>'

                        attrs_html = ""
                        for k, v in (item.attributes or {}).items():
                            attrs_html += f'<span style="color:#6b7280;font-size:0.82em;margin-right:12px;">{k}: <strong style="color:#374151;">{v}</strong></span>'

                        list_html = f'<span style="color:#9ca3af;text-decoration:line-through;font-size:0.88em;margin-left:8px;">Lista: ${item.list_price:.2f}</span>' if item.list_price > item.price else ""

                        avail_html = ""
                        if item.store_qty > 0:
                            avail_html += f'<span style="color:#16a34a;font-size:0.85em;font-weight:600;">{item.store_qty} en tienda &nbsp;</span>'
                        if item.total_qty > 0:
                            avail_html += f'<span style="color:#6b7280;font-size:0.85em;">{item.total_qty} total</span>'

                        part_num_html = f'<span style="color:#6b7280;font-size:0.82em;">Part #: <strong>{item.part_number}</strong></span>' if item.part_number else ""

                        img_html = f'<img src="{item.image_url}" style="width:80px;height:80px;object-fit:contain;border-radius:6px;border:1px solid #e5e7eb;margin-right:14px;flex-shrink:0;" onerror="this.style.display=\'none\'"/>' if item.image_url else '<div style="width:80px;height:80px;background:#f3f4f6;border-radius:6px;margin-right:14px;flex-shrink:0;"></div>'

                        st.markdown(
                            f"""
                            <div style="border-left:4px solid {border_color};border-radius:12px;background:white;padding:14px 18px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                                <div style="display:flex;align-items:flex-start;gap:4px;">
                                    {img_html}
                                    <div style="flex:1;min-width:0;">
                                        <div style="margin-bottom:5px;">{badge_html}{pos_html}</div>
                                        <div style="font-size:1.05em;font-weight:700;color:#111827;margin-bottom:2px;">{item.brand} {item.description}</div>
                                        <div style="margin-bottom:5px;">{part_num_html}</div>
                                        <div style="margin-bottom:8px;flex-wrap:wrap;">{attrs_html}</div>
                                        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;">
                                            <div>
                                                <span style="font-size:1.5em;font-weight:800;color:{border_color};">${item.price:.2f}</span>
                                                {list_html}
                                            </div>
                                            <div style="text-align:right;">
                                                <div style="font-weight:600;color:#374151;font-size:0.9em;">{item.store}</div>
                                                <div>{avail_html}</div>
                                                <div style="color:#6b7280;font-size:0.82em;">{item.eta}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # ---- QUOTE TOTALS ----
                    chosen_part_cost = display_items[0].price
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
                        st.button(T["square_btn"], use_container_width=True)


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
else:
    render_help()

st.markdown(f'<p class="footer-text">{T["footer"]}</p>', unsafe_allow_html=True)
