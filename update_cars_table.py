import sqlite3
from config import DB_NAME

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

columns = [
    ("mileage", "TEXT"),
    ("body_condition", "TEXT"),
    ("fuel_efficiency", "TEXT"),
    ("engine_performance", "TEXT")
]

for column_name, column_type in columns:
    try:
        cursor.execute(f"ALTER TABLE cars ADD COLUMN {column_name} {column_type}")
        print(f"✅ Added column: {column_name}")
    except:
        print(f"⏩ Skipped (already exists): {column_name}")

conn.commit()
conn.close()
