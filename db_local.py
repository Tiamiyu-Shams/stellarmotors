import sqlite3
from werkzeug.security import generate_password_hash
import os
from config import DB_NAME

# ----------- CONNECTION (LOCAL SQLITE) ------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ----------- GENERIC QUERY HELPERS -------------
def query(sql, args=()):
    with get_db_connection() as conn:
        cur = conn.execute(sql, args)
        rows = cur.fetchall()
        return rows


def modify(sql, args=()):
    with get_db_connection() as conn:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid


# ----------- INITIALIZE DATABASE TABLES ------------
def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()

        # USERS TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # SELLERS TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_email TEXT,
                phone TEXT,
                address TEXT,
                about TEXT,
                photo TEXT
            )
        """)

        # CARS TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                seller_id INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES sellers(id)
            )
        """)

        # CAR IMAGES TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS car_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER,
                image_path TEXT,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """)

        conn.commit()
        print("✅ SQLite local DB initialized")


# ----------- SEED SAMPLE DATA -------------------
def seed_data():
    with get_db_connection() as conn:
        cur = conn.cursor()

        # ADMIN USER
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            pw = generate_password_hash("password123")
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        ("admin", pw))
            print("➡️ Default admin user created")

        # SELLERS
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
                VALUES (?, ?, ?, ?, ?, ?)
            """, sellers)

            print("➡️ Sample sellers added")

        # CARS
        cur.execute("SELECT COUNT(*) FROM cars")
        if cur.fetchone()[0] == 0:
            cars = [
                ("2023 Executive Sedan", "Luxury sedan.", 45000,
                 "/static/images/sedan.jpg", "Alice Johnson", None, "Sedan",
                 "10,000 km", "Excellent", "15 km/L", "V6 Turbo", 1),

                ("2022 Sport Coupe", "Sport coupe.", 38500,
                 "/static/images/coupe.jpg", "Bob Smith", None, "Coupe",
                 "8,000 km", "Very Good", "14 km/L", "2.0L Turbo", 2),

                ("2021 Family SUV", "Spacious SUV.", 29900,
                 "/static/images/suv.jpg", "Carol White", None, "SUV",
                 "20,000 km", "Good", "12 km/L", "3.0L V6", 3),
            ]

            cur.executemany("""
                INSERT INTO cars (
                    title, description, price, image, seller_name, seller_photo,
                    category, mileage, body_condition, fuel_efficiency,
                    engine_performance, seller_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cars)

            print("➡️ Sample cars added")

        conn.commit()
