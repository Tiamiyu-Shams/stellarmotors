import psycopg2
import os
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL")

# ------------------------
# CONNECTION
# ------------------------
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ------------------------
# UNIFIED QUERY HELPERS
# ------------------------
def db_query(sql, params=()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def db_modify(sql, params=()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    rowid = cur.rowcount
    cur.close()
    conn.close()
    return rowid


# ------------------------
# INITIAL SETUP
# ------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sellers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        contact_email TEXT,
        phone TEXT,
        address TEXT,
        about TEXT,
        photo TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        price REAL,
        image TEXT,
        seller_name TEXT,
        seller_photo TEXT,
        category TEXT,
        mileage TEXT,
        body_condition TEXT,
        fuel_efficiency TEXT,
        engine_performance TEXT,
        seller_id INTEGER REFERENCES sellers(id),
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS car_images (
        id SERIAL PRIMARY KEY,
        car_id INTEGER REFERENCES cars(id),
        image_path TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("🚀 PostgreSQL DB initialized on Render")


def seed_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", generate_password_hash("password123"))
        )
        print("➡️ Created admin user")

    conn.commit()
    cur.close()
    conn.close()
