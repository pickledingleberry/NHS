DIAGNOSTIC_CODES = {
    "P0300": {
        "title": "Múltiples fallos de encendido detectados / Random Misfire Detected",
        "desc": "El motor está fallando de forma aleatoria en varios cilindros. Esto causa pérdida de potencia, vibración y humo.",
        "causes": ["Bujías gastadas", "Bobinas de encendido defectuosas", "Fuga de vacío", "Presión de gasolina baja"],
        "parts": ["bujias", "bobina", "filtro de gasolina"],
    },
    "P0301": {
        "title": "Fallo de encendido en Cilindro 1 / Cylinder 1 Misfire Detected",
        "desc": "La computadora detectó que el cilindro número 1 no está haciendo combustión correctamente.",
        "causes": ["Bujía del cilindro 1 quemada", "Bobina del cilindro 1 fallando", "Inyector tapado"],
        "parts": ["bujias", "bobina"],
    },
    "P0302": {
        "title": "Fallo de encendido en Cilindro 2 / Cylinder 2 Misfire Detected",
        "desc": "La computadora detectó que el cilindro número 2 no está haciendo combustión correctamente.",
        "causes": ["Bujía del cilindro 2 quemada", "Bobina del cilindro 2 fallando", "Inyector tapado"],
        "parts": ["bujias", "bobina"],
    },
    "P0303": {
        "title": "Fallo de encendido en Cilindro 3 / Cylinder 3 Misfire Detected",
        "desc": "La computadora detectó que el cilindro número 3 no está haciendo combustión correctamente.",
        "causes": ["Bujía del cilindro 3 quemada", "Bobina del cilindro 3 fallando", "Inyector tapado"],
        "parts": ["bujias", "bobina"],
    },
    "P0304": {
        "title": "Fallo de encendido en Cilindro 4 / Cylinder 4 Misfire Detected",
        "desc": "La computadora detectó que el cilindro número 4 no está haciendo combustión correctamente.",
        "causes": ["Bujía del cilindro 4 quemada", "Bobina del cilindro 4 fallando", "Inyector tapado"],
        "parts": ["bujias", "bobina"],
    },
    "P0420": {
        "title": "Eficiencia del Catalizador por debajo del límite / Catalyst Efficiency Below Threshold (Bank 1)",
        "desc": "El convertidor catalítico no está limpiando los gases de escape de manera eficiente.",
        "causes": ["Catalizador dañado o tapado", "Sensor de Oxígeno (O2) defectuoso", "Fuga en el escape"],
        "parts": ["sensor o2"],
    },
    "P0171": {
        "title": "Mezcla de aire/combustible demasiado pobre / System Too Lean (Bank 1)",
        "desc": "El motor está recibiendo demasiado aire o muy poca gasolina.",
        "causes": ["Sensor de Masa de Aire (MAF) sucio/roto", "Fugas de vacío en mangueras", "Bomba de gasolina débil"],
        "parts": ["sensor maf", "filtro de gasolina"],
    },
    "P0172": {
        "title": "Mezcla de aire/combustible demasiado rica / System Too Rich (Bank 1)",
        "desc": "El motor está recibiendo demasiada gasolina o muy poco aire.",
        "causes": ["Filtro de aire sumamente obstruido", "Sensor de Oxígeno fallando", "Inyector goteando"],
        "parts": ["filtro de aire", "sensor o2"],
    },
    "P0113": {
        "title": "Sensor de temperatura de aire de admisión alto / IAT Sensor 1 Circuit High",
        "desc": "El sensor que mide la temperatura del aire que entra al motor tiene un voltaje alto.",
        "causes": ["Sensor MAF/IAT defectuoso", "Cableado dañado o desconectado"],
        "parts": ["sensor maf"],
    },
    "P0115": {
        "title": "Sensor de temperatura del anticongelante / Engine Coolant Temp Circuit Malfunction",
        "desc": "La computadora no recibe lectura correcta del sensor de temperatura del refrigerante.",
        "causes": ["Sensor ECT dañado", "Termostato pegado abierto", "Nivel de anticongelante bajo"],
        "parts": ["termostato"],
    },
    "P0128": {
        "title": "Temperatura del refrigerante por debajo del termostato / Coolant Temp Below Thermostat Regulating Temp",
        "desc": "El motor tarda demasiado en calentarse o se mantiene muy frío en carretera.",
        "causes": ["Termostato pegado abierto (se queda pasando anticongelante)", "Sensor ECT dañado"],
        "parts": ["termostato"],
    },
    "P0505": {
        "title": "Control de aire de marcha mínima / Idle Control System Malfunction",
        "desc": "El motor tiembla en los semáforos, se apaga, o las revoluciones suben y bajan solas.",
        "causes": ["Cuerpo de aceleración sucio o descalibrado", "Válvula IAC defectuosa", "Fuga de vacío"],
        "parts": ["cuerpo de aceleracion"],
    },
}


def lookup_code(code: str) -> dict | None:
    """Analyze OBD-II code and return Spanish description, possible causes, and related parts."""
    clean = code.strip().upper()
    return DIAGNOSTIC_CODES.get(clean)
