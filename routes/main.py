import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from db import get_db_connection

from flask import current_app
from flask_mail import Message

#from app import mail   # ensure mail is imported from your main app

# routes/main.py





UPLOAD_FOLDER = 'static/uploads'

main_bp = Blueprint("main", __name__)

""" @main_bp.route("/")
def index():
    conn = get_db_connection()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC LIMIT 9").fetchall()
    conn.close()
    return render_template("index.html", cars=cars)
 """

@main_bp.route("/")
def index():
    conn = get_db_connection()

    # Read filter inputs from query parameters
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    sort = request.args.get("sort", "")


    # Base SQL query
    query = "SELECT * FROM cars WHERE 1=1"
    params = {}

    # Search by text
    if search:
        query += " AND (title LIKE :search OR description LIKE :search)"
        params["search"] = f"%{search}%"

    # Category filter
    if category:
        query += " AND category = :category"
        params["category"] = category

    # Minimum price
    if min_price:
        query += " AND price >= :min_price"
        params["min_price"] = float(min_price)

    # Maximum price
    if max_price:
        query += " AND price <= :max_price"
        params["max_price"] = float(max_price)

    # Sorting rules
    if sort == "price_asc":
        query += " ORDER BY price ASC"
    elif sort == "price_desc":
        query += " ORDER BY price DESC"
    elif sort == "newest":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"   # Default

    # Execute SQL
    cars = conn.execute(query, params).fetchall()

    # Retrieve categories for the dropdown
    categories = conn.execute("SELECT DISTINCT category FROM cars").fetchall()

    conn.close()

    return render_template(
        "index.html",
        cars=cars,
        categories=categories,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort=sort
    )


# --- MAIN: BROWSE CARS WITH SEARCH, SORT & PAGINATION ---
@main_bp.route("/cars")
def cars():
    conn = get_db_connection()

    # --- Get search, category, sorting, and pagination parameters ---
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "date_added")  # default: newest first
    page = int(request.args.get("page", 1))
    per_page = 6  # cars per page

    # --- Base query ---
    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    # --- Add search filter ---
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term])

    # --- Add category filter ---
    if category:
        query += " AND category = ?"
        params.append(category)

    # --- Sorting options ---
    if sort_by == "price":
        query += " ORDER BY price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY price DESC"
    elif sort_by == "title":
        query += " ORDER BY title COLLATE NOCASE ASC"
    else:
        query += " ORDER BY date_added DESC"  # newest first

    # --- Pagination ---
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    # --- Fetch data ---
    cars = conn.execute(query, params).fetchall()

    # --- Count total for pagination ---
    count_query = "SELECT COUNT(*) FROM cars WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (title LIKE ? OR description LIKE ?)"
        count_params.extend([like_term, like_term])
    if category:
        count_query += " AND category = ?"
        count_params.append(category)

    total_cars = conn.execute(count_query, count_params).fetchone()[0]
    total_pages = (total_cars + per_page - 1) // per_page

    # --- Get distinct categories for the dropdown ---
    categories = [row["category"] for row in conn.execute("SELECT DISTINCT category FROM cars WHERE category IS NOT NULL").fetchall()]

    conn.close()

    return render_template(
        "cars.html",
        cars=cars,
        categories=categories,
        search=search,
        category=category,
        sort_by=sort_by,
        page=page,
        total_pages=total_pages,
    )


@main_bp.route('/cars/<int:car_id>')
def car_detail(car_id):
    conn = get_db_connection()
    car = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    if not car:
        #return "Car not found", 404
        conn.close()
        flash("Car not found", "error")
        return redirect(url_for('main.cars'))

    # Safely load the seller if car['seller_id'] exists
    seller = None
    if car['seller_id']:
        seller = conn.execute("SELECT * FROM sellers WHERE id = ?", (car['seller_id'],)).fetchone()
    
    #seller = conn.execute("SELECT * FROM sellers WHERE id = ?", (car['seller_id'],)).fetchone()
    car_images = conn.execute("SELECT * FROM car_images WHERE car_id = ?", (car_id,)).fetchall()
    conn.close()

    return render_template("car_detail.html", car=car, seller=seller, car_images=car_images)


@main_bp.route('/add_car', methods=['GET', 'POST'])
def add_car():
    conn = get_db_connection()
    sellers = conn.execute("SELECT * FROM sellers").fetchall()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        price = request.form.get('price', 0)
        category = request.form.get('category', '')
        seller_id = request.form.get('seller_id')
        mileage = request.form.get('mileage', '')
        body_condition = request.form.get('body_condition', '')
        fuel_efficiency = request.form.get('fuel_efficiency', '')
        engine_performance = request.form.get('engine_performance', '')


        # --- Save main image ---
        main_image_file = request.files.get('main_image')
        main_image_path = None
        if main_image_file:
            filename = secure_filename(main_image_file.filename)
            main_image_path = os.path.join(UPLOAD_FOLDER, filename)
            full_path = os.path.join(current_app.root_path, main_image_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            main_image_file.save(full_path)

        # --- Insert new car ---
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cars 
            (title, description, price, category, seller_id, image, mileage, body_condition, fuel_efficiency, engine_performance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, description, price, category, seller_id, '/' + main_image_path,
            mileage, body_condition, fuel_efficiency, engine_performance))

        car_id = cursor.lastrowid

        # --- Handle multiple images ---
        files = request.files.getlist('images')
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                full_path = os.path.join(current_app.root_path, image_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

                cursor.execute(
                    "INSERT INTO car_images (car_id, image_path) VALUES (?, ?)",
                    (car_id, '/' + image_path)
                )

        conn.commit()
        conn.close()

        flash("Car uploaded successfully!", "success")
        return redirect(url_for('main.cars'))

    conn.close()
    return render_template('add_car.html', sellers=sellers)



# --------------------------------------------------------
# CONTACT SELLER ROUTE
# --------------------------------------------------------
@main_bp.route('/contact_seller/<int:seller_id>', methods=['GET', 'POST'])
def contact_seller(seller_id):
    from flask import flash  # if not already imported at the top
    import sqlite3

    conn = sqlite3.connect('cars.db')
    conn.row_factory = sqlite3.Row
    seller = conn.execute("SELECT * FROM sellers WHERE id = ?", (seller_id,)).fetchone()
    conn.close()

    if not seller:
        flash("Seller not found.", "error")
        return redirect(url_for('main.cars'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # For now, we’ll just flash a success message — later we can save this in DB
        flash(f"Message sent successfully to {seller['name']}!", "success")
        return redirect(url_for('main.cars'))

    return render_template("contact_seller.html", seller=seller)


# --------------------------------------------------------
# SEND MESSAGE TO SELLER ROUTE
# --------------------------------------------------------
@main_bp.route("/send_message", methods=["POST"])
def send_message():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    seller_phone = request.form.get("seller_phone")
    seller_email = request.form.get("seller_email")
    seller_name = request.form.get("seller_name")
    car_title = request.form.get("car_title")

    full_message = (
        f"New Inquiry About {car_title}\n"
        f"From: {name}\n"
        f"Email: {email}\n"
        f"Message:\n{message}"
    )

    # ----------------------------------------------
    # 1. SEND AUTOMATIC WHATSAPP MESSAGE
    # ----------------------------------------------
    import urllib.parse

    wa_text = urllib.parse.quote(
        f"Hello {seller_name},\n\n"
        f"You have a new inquiry about *{car_title}*.\n\n"
        f"From: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}"
    )

    whatsapp_url = f"https://wa.me/{seller_phone}?text={wa_text}"

    # ----------------------------------------------
    # 2. SEND EMAIL TO SELLER (GMAIL / SMTP)
    # ----------------------------------------------
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(full_message)
        msg["Subject"] = f"New Message About {car_title}"
        msg["From"] = email
        msg["To"] = seller_email

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()

        # Optional: store these in environment variables
        smtp.login("YOUR_GMAIL_ADDRESS", "YOUR_APP_PASSWORD")

        smtp.sendmail(email, seller_email, msg.as_string())
        smtp.quit()

    except Exception as e:
        print("Email error:", e)

    # ----------------------------------------------
    # 3. OPTIONAL: SAVE MESSAGE TO DATABASE
    # ----------------------------------------------
    # new_message = Message(
    #     name=name,
    #     email=email,
    #     seller_id=seller_id,
    #     car_title=car_title,
    #     content=message
    # )
    # db.session.add(new_message)
    # db.session.commit()

    # ----------------------------------------------
    # 4. REDIRECT USER TO WHATSAPP AUTOMATICALLY
    # ----------------------------------------------
    return redirect(whatsapp_url)









