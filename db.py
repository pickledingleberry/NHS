import sqlite3
from datetime import datetime

DB_PATH = "taller_del_barrio.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for Quotes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            customer_name TEXT,
            vin TEXT,
            vehicle_desc TEXT,
            part_name TEXT,
            part_brand TEXT,
            part_number TEXT,
            part_cost REAL,
            labor_hours REAL,
            discount REAL,
            tax REAL,
            grand_total REAL,
            store TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def save_quote(
    customer_name: str,
    vin: str,
    vehicle_desc: str,
    part_name: str,
    part_brand: str,
    part_number: str,
    part_cost: float,
    labor_hours: float,
    discount: float,
    tax: float,
    grand_total: float,
    store: str,
) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    cursor.execute(
        """
        INSERT INTO quotes (
            created_at, customer_name, vin, vehicle_desc, part_name,
            part_brand, part_number, part_cost, labor_hours, discount, tax, grand_total, store
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            created_at,
            customer_name.strip(),
            vin.strip().upper(),
            vehicle_desc.strip(),
            part_name.strip(),
            part_brand.strip(),
            part_number.strip(),
            part_cost,
            labor_hours,
            discount,
            tax,
            grand_total,
            store,
        ),
    )

    quote_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return quote_id


def get_quotes(search_query: str = "") -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search_query:
        q = f"%{search_query}%"
        cursor.execute(
            """
            SELECT * FROM quotes 
            WHERE customer_name LIKE ? OR vin LIKE ? OR vehicle_desc LIKE ? OR part_name LIKE ?
            ORDER BY id DESC
        """,
            (q, q, q, q),
        )
    else:
        cursor.execute("SELECT * FROM quotes ORDER BY id DESC LIMIT 50")

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
