import streamlit as st
import requests
import json
import time

# --- 1. PRO SHOP BRANDING ---
st.set_page_config(page_title="Neighborhood Auto Shop Portal", layout="centered")

if "lang" not in st.session_state:
    st.session_state.lang = "Español"

# Language Dictionary Matrix
T = {
    "Español": {
        "subtitle": "🏠 Sistema de Partes y Cotizaciones",
        "vin_lbl": "Escribe el número VIN de 17 dígitos:",
        "part_lbl": "Número de Parte o Nombre (ej: Balatas, Alternador):",
        "toggle_cheap": "🏆 Resaltar solo el más barato",
        "labor_lbl": "Horas de Trabajo Estimadas ($100/hr):",
        "btn_calc": "🔍 Buscar y Calcular Todo",
        "cheapest_alert": "🏆 ¡EL MÁS BARATO!",
        "vin_ok": "🚗 Vehículo Decodificado Correctamente:",
        "labor_cost": "Costo de Mano de Obra",
        "grand_total": "TOTAL DE LA COTIZACIÓN"
    },
    "English": {
        "subtitle": "🏠 Parts Lookup & Quote System",
        "vin_lbl": "Type 17-digit VIN number:",
        "part_lbl": "Part Number or Name (e.g. Brake Pads, Alternator):",
        "toggle_cheap": "🏆 Highlight Cheapest Only",
        "labor_lbl": "Estimated Labor Hours ($100/hr):",
        "btn_calc": "🔍 Search & Calculate Total",
        "cheapest_alert": "🏆 CHEAPEST OPTION!",
        "vin_ok": "🚗 Vehicle Successfully Decoded:",
        "labor_cost": "Labor Cost",
        "grand_total": "GRAND ESTIMATE TOTAL"
    }
}[st.session_state.lang]

# Centered Custom Shop Header
st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 0px;'>Neighborhood Auto Shop</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #6B7280; font-size: 1.1em;'>{T['subtitle']}</p>", unsafe_allow_html=True)

# Clean Lang Toggle Row
col_space, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("🇲🇽 / 🇺🇸 Idioma"):
        st.session_state.lang = "English" if st.session_state.lang == "Español" else "Español"
        st.rerun()

st.write("---")

# --- 2. FREE GOVERNMENT VIN DECODER ---
def decode_vin(vin):
    if len(vin) < 17: return None
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    try:
        res = requests.get(url).json().get('Results', [])
        car = {"Year": "", "Make": "", "Model": "", "Engine": ""}
        for item in res:
            v, val = item.get('Variable'), item.get('Value')
            if v == "Model Year": car["Year"] = val
            elif v == "Make": car["Make"] = val
            elif v == "Model": car["Model"] = val
            elif v == "Displacement (L)": car["Engine"] = f"{val}L" if val else ""
        if car["Year"] and car["Make"]: return car
    except: return None
    return None

# --- 3. INPUT FORM FIELDS ---
vin_in = st.text_input(T["vin_lbl"], max_chars=17).upper()
car_info = None

if vin_in and len(vin_in) == 17:
    car_info = decode_vin(vin_in)
    if car_info:
        st.success(f"{T['vin_ok']} {car_info['Year']} {car_info['Make']} {car_info['Model']} {car_info['Engine']}")
    else:
        st.error("VIN inválido / Invalid VIN")

part_in = st.text_input(T["part_lbl"], placeholder="e.g., H6-DLG")
show_cheapest = st.toggle(T["toggle_cheap"], value=False)
labor_hours = st.number_input(T["labor_lbl"], min_value=0.0, max_value=20.0, value=1.0, step=0.5)

st.write("---")

# --- 4. DATA ENGINE AND RESULTS CALCULATOR ---
if st.button(T["btn_calc"], type="primary"):
    if not part_in:
        st.warning("Por favor ingrese una parte / Please enter a part")
    else:
        with st.spinner("Buscando refacciones..."):
            # Mock Data Simulator representing our core scrapers
            scraped_data = [
                {"store": "Factory Motor Parts (FMP)", "brand": "ACDelco Professional", "price": 85.00, "eta": "20 mins"},
                {"store": "AutoZone Pro", "brand": "Duralast Gold", "price": 92.50, "eta": "En Tienda / In Stock"},
                {"store": "O'Reilly First Call", "brand": "Brakebest Select", "price": 79.99, "eta": "Mañana / Tomorrow"}
            ]
            
            # Filter and sort
            scraped_data.sort(key=lambda x: x["price"])
            
            if show_cheapest:
                # Filter down to display only the single lowest entry
                display_items = [scraped_data[0]]
            else:
                display_items = scraped_data

            # Display individual cards
            for idx, item in enumerate(display_items):
                is_num_one = (item["price"] == scraped_data[0]["price"])
                
                if is_num_one and show_cheapest:
                    st.markdown(f"### **{T['cheapest_alert']}**")
                    st.success(f"**{item['store']}** — *{item['brand']}*\n\n💰 **Precio:** ${item['price']:.2f} | 🚚 **Disponibilidad:** {item['eta']}")
                else:
                    st.info(f"**{item['store']}** — *{item['brand']}*\n\n💰 **Precio:** ${item['price']:.2f} | 🚚 **Disponibilidad:** {item['eta']}")

            # --- MATH TOTALS MATRIX ---
            chosen_part_cost = display_items[0]["price"] # Baseline math off current selected option
            parts_markup = chosen_part_cost * 1.30 # Automatically adding our 30% shop profit margin
            calculated_labor = labor_hours * 100.00
            grand_total = parts_markup + calculated_labor

            st.write("---")
            st.markdown(f"### 🧮 Resumen de Cuenta / Totals")
            
            col_left, col_right = st.columns(2)
            with col_left:
                st.metric(label=f"Partes (+ 30% Markup)", value=f"${parts_markup:.2f}")
                st.metric(label=f"{T['labor_cost']} ({labor_hours} hrs)", value=f"${calculated_labor:.2f}")
            with col_right:
                st.metric(label=f"⭐ {T['grand_total']}", value=f"${grand_total:.2f}")
                
                # Handheld Square trigger payload setup
                st.markdown(f"**Square Machine Total:** `${grand_total:.2f}`")
                st.button("💳 Enviar cobro a Terminal Square / Send to Square Device", use_container_width=True)
