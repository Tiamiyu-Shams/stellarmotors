import sqlite3
from config import DB_NAME

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sellers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_info TEXT,
    photo TEXT
)
""")

conn.commit()
conn.close()

print("✅ Sellers table created successfully.")
