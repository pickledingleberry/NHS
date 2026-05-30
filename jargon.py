JARGON_MAP = {
    # Brakes
    "balatas": "brake pads",
    "balata": "brake pads",
    "discos de freno": "brake rotor",
    "discos": "brake rotor",
    "disco": "brake rotor",
    "caliper": "brake caliper",
    "calibrador": "brake caliper",
    "tambores": "brake drum",
    "tambor": "brake drum",
    "zapatas": "brake shoe",
    "zapatas de freno": "brake shoe",
    "manguera de freno": "brake hose",
    # Ignition / Spark Plugs
    "bujias": "spark plugs",
    "bujia": "spark plugs",
    "bujías": "spark plugs",
    "bujía": "spark plugs",
    "bobina": "ignition coil",
    "bobinas": "ignition coil",
    "cables de bujia": "spark plug wires",
    "cables de bujias": "spark plug wires",
    # Filters
    "filtro de aceite": "oil filter",
    "filtro aceite": "oil filter",
    "filtro de aire": "air filter",
    "filtro aire": "air filter",
    "filtro de cabina": "cabin air filter",
    "filtro cabina": "cabin air filter",
    "filtro de gasolina": "fuel filter",
    "filtro gasolina": "fuel filter",
    # Engine / Belt / Cooling
    "alternador": "alternator",
    "marcha": "starter",
    "motor de arranque": "starter",
    "bateria": "battery",
    "batería": "battery",
    "bomba de agua": "water pump",
    "termostato": "thermostat",
    "banda": "serpentine belt",
    "correa": "serpentine belt",
    "banda de accesorios": "serpentine belt",
    "radiador": "radiator",
    "manguera de radiador": "radiator hose",
    # Suspension / Steer / Axles
    "amortiguadores": "shocks",
    "amortiguador": "shocks",
    "strut": "strut",
    "horquilla": "control arm",
    "horquillas": "control arm",
    "brazo de control": "control arm",
    "cacahuate": "sway bar link",
    "cacahuates": "sway bar link",
    "tornillo estabilizador": "sway bar link",
    "terminal de direccion": "tie rod end",
    "terminal": "tie rod end",
    "rotula": "ball joint",
    "rotulas": "ball joint",
    "balero": "wheel bearing",
    "balero doble": "wheel bearing",
    "rodamiento": "wheel bearing",
    "flecha": "cv axle",
    "eje cv": "cv axle",
    "junta homocinetica": "cv joint",
    # Diagnostics / Sensors
    "sensor o2": "oxygen sensor",
    "sensor de oxigeno": "oxygen sensor",
    "sensor de oxígeno": "oxygen sensor",
    "maf": "mass air flow",
    "sensor maf": "mass air flow",
    "cuerpo de aceleracion": "throttle body",
    "sensor abs": "abs wheel speed sensor",
}


def map_jargon(query: str) -> str:
    """Translate common Spanish mechanic jargon into official English supplier catalog keywords."""
    clean = query.strip().lower()
    # Check exact match
    if clean in JARGON_MAP:
        return JARGON_MAP[clean]

    # Check substring matches
    for jargon, english in JARGON_MAP.items():
        if jargon in clean:
            return clean.replace(jargon, english)

    return query
