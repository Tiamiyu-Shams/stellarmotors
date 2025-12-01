import sqlite3
from config import DB_NAME
from werkzeug.security import generate_password_hash

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Create or update all tables with consistent structure.
    Adds support for sellers, car details, and multiple images.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # --- USERS TABLE (Admin Login) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # --- SELLERS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_email TEXT,
                phone TEXT,
                address TEXT,
                about TEXT
            )
        """)

        # --- CARS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                price REAL,
                image TEXT,                -- main image (for listing card)
                seller_name TEXT,           -- backward compatible
                seller_photo TEXT,          -- backward compatible
                category TEXT,
                mileage TEXT,
                body_condition TEXT,
                fuel_efficiency TEXT,
                engine_performance TEXT,
                seller_id INTEGER,          -- new relation
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- NEW FIELD
                FOREIGN KEY (seller_id) REFERENCES sellers(id)
            )
        """)



        # --- CAR IMAGES TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS car_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """)

        conn.commit()


        # Table for multiple car images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS car_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER,
                image_path TEXT,
                FOREIGN KEY (car_id) REFERENCES cars (id)
            )
        """)

        # --- Update sellers table to include photo if it doesn't exist ---
        cursor.execute("PRAGMA table_info(sellers);")
        columns = [col[1] for col in cursor.fetchall()]
        if 'photo' not in columns:
            cursor.execute("ALTER TABLE sellers ADD COLUMN photo TEXT;")




        # --- SAFE MIGRATIONS (add missing columns to existing DBs) ---
        cursor.execute("PRAGMA table_info(cars)")
        cols = [row[1] for row in cursor.fetchall()]

        alter_statements = []
        if "mileage" not in cols:
            alter_statements.append("ALTER TABLE cars ADD COLUMN mileage TEXT")
        if "body_condition" not in cols:
            alter_statements.append("ALTER TABLE cars ADD COLUMN body_condition TEXT")
        if "fuel_efficiency" not in cols:
            alter_statements.append("ALTER TABLE cars ADD COLUMN fuel_efficiency TEXT")
        if "engine_performance" not in cols:
            alter_statements.append("ALTER TABLE cars ADD COLUMN engine_performance TEXT")
        if "seller_id" not in cols:
            alter_statements.append("ALTER TABLE cars ADD COLUMN seller_id INTEGER REFERENCES sellers(id)")

        for stmt in alter_statements:
            cursor.execute(stmt)

        
        conn.commit()
        print("✅ Database initialized successfully.")


def seed_data():
    """Insert default admin user and sample data if tables are empty."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # --- Admin user ---
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            pw_hash = generate_password_hash("password123")
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", pw_hash))
            print("✅ Default admin created: username='admin', password='password123'")

        # --- Sample Sellers ---
        cursor.execute("SELECT COUNT(*) FROM sellers")
        if cursor.fetchone()[0] == 0:
            sellers = [
                ("Alice Johnson", "alice@example.com", "08012345678", "Lagos", "Trusted luxury car dealer."),
                ("Bob Smith", "bob@example.com", "08123456789", "Abuja", "Certified used car dealer."),
                ("Carol White", "carol@example.com", "09098765432", "Port Harcourt", "SUV specialist."),
            ]
            cursor.executemany(
                "INSERT INTO sellers (name, contact_email, phone, address, about) VALUES (?, ?, ?, ?, ?)",
                sellers
            )
            print("✅ Sample sellers added.")

        # --- Sample Cars ---
        cursor.execute("SELECT COUNT(*) FROM cars")
        if cursor.fetchone()[0] == 0:
            cars = [
                ("2023 Executive Sedan", "Luxury sedan with premium features.", 45000,
                 "/static/images/sedan.jpg", "Alice Johnson", "/static/images/seller1.jpg", "Sedan",
                 "10,000 km", "Excellent", "15 km/L", "V6 Turbo Engine", 1),
                ("2022 Sport Coupe", "Sport coupe with thrilling performance.", 38500,
                 "/static/images/coupe.jpg", "Bob Smith", "/static/images/seller2.jpg", "Coupe",
                 "8,000 km", "Very Good", "14 km/L", "2.0L Turbo", 2),
                ("2021 Family SUV", "Spacious SUV perfect for family life.", 29900,
                 "/static/images/suv.jpg", "Carol White", "/static/images/seller3.jpg", "SUV",
                 "20,000 km", "Good", "12 km/L", "3.0L V6", 3),
            ]
            cursor.executemany("""
                INSERT INTO cars
                (title, description, price, image, seller_name, seller_photo, category,
                 mileage, body_condition, fuel_efficiency, engine_performance, seller_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cars)
            print("✅ Sample cars added.")

        conn.commit()
