import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

DB_URL = os.getenv("DATABASE_URL")


# -------------------------------------------------
# POSTGRES CONNECTION
# -------------------------------------------------
def get_db_connection():
    conn = psycopg2.connect(DB_URL, sslmode="require")
    return conn


# -------------------------------------------------
# QUERY HELPERS
# -------------------------------------------------
def query(sql, args=()):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    return rows


def modify(sql, args=()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    try:
        last_id = cur.fetchone()[0]
    except:
        last_id = None
    conn.close()
    return last_id


# -------------------------------------------------
# INITIAL DATABASE SCHEMA
# -------------------------------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS TABLE (for admin login)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # SELLERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            contact_email TEXT,
            phone TEXT,
            address TEXT,
            about TEXT,
            photo TEXT
        );
    """)

    # CARS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            price REAL,
            category TEXT,
            mileage TEXT,
            body_condition TEXT,
            fuel_efficiency TEXT,
            engine_performance TEXT,
            seller_id INTEGER REFERENCES sellers(id),
            main_image TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # MULTIPLE IMAGES TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS car_images (
            id SERIAL PRIMARY KEY,
            car_id INTEGER REFERENCES cars(id),
            image_path TEXT
        );
    """)

    conn.commit()
    conn.close()
    print("🚀 PostgreSQL DB initialized successfully!")


# -------------------------------------------------
# DEFAULT SEED DATA
# -------------------------------------------------
def seed_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # ------------------------
    # ADMIN ACCOUNT
    # ------------------------
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        pw = generate_password_hash("password123")
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", pw)
        )

    # ------------------------
    # SELLER ENTRIES
    # ------------------------
    cur.execute("SELECT COUNT(*) FROM sellers")
    if cur.fetchone()[0] == 0:
        sellers = [
            ("Alice Johnson", "alice@example.com", "08012345678", "Lagos",
             "Trusted luxury car dealer.", None),
            ("Bob Smith", "bob@example.com", "08123456789", "Abuja",
             "Certified used car dealer.", None),
            ("Carol White", "carol@example.com", "09098765432", "Port Harcourt",
             "SUV specialist.", None),
        ]
        cur.executemany("""
            INSERT INTO sellers (name, contact_email, phone, address, about, photo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, sellers)

    # ------------------------
    # CAR SEED DATA
    # ------------------------
    cur.execute("SELECT COUNT(*) FROM cars")
    if cur.fetchone()[0] == 0:
        cars = [
            ("2023 Executive Sedan", "Luxury sedan.", 24500000, "Sedan",
             "10,000 km", "Excellent", "15 km/L", "V6 Turbo Engine", 1,
             "/static/images/sedan.jpg"),

            ("2022 Sport Coupe", "Sport coupe.", 13850000, "Coupe",
             "8,000 km", "Very Good", "14 km/L", "2.0L Turbo", 2,
             "/static/images/coupe.jpg"),

            ("2021 Family SUV", "Spacious SUV.", 19900000, "SUV",
             "20,000 km", "Good", "12 km/L", "3.0L V6", 3,
             "/static/images/suv.jpg"),
        ]

        cur.executemany("""
            INSERT INTO cars (
                title, description, price, category, mileage, body_condition,
                fuel_efficiency, engine_performance, seller_id, main_image
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, cars)

    conn.commit()
    conn.close()
    print("🌱 Database seeded successfully!")
