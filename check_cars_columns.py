import sqlite3
import os

# Try common DB filenames used in this project
candidates = ["database.db", "cars.db", "stellar.db", "car_dealer.db"]

found = False
for fn in candidates:
    if os.path.exists(fn):
        found = True
        print(f"Using DB file: {fn}")
        conn = sqlite3.connect(fn)
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(cars);")
            cols = cursor.fetchall()
            if not cols:
                print("→ Table 'cars' does not exist in this DB.")
            else:
                print("Columns in 'cars':")
                for c in cols:
                    print("   ", c[1])   # c[1] is column name
        finally:
            conn.close()
        break

if not found:
    print("No DB file found. Check which DB your app uses (DB_NAME in config.py).")
