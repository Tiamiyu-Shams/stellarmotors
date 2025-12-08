import os
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
)

from flask_mail import Message
from db import get_db_connection  # Auto switches between SQLite or PostgreSQL

main_bp = Blueprint("main", __name__)

UPLOAD_FOLDER = "static/uploads"


# -------------------------------------------------
# HOME PAGE (Search + Filters + Sorting)
# -------------------------------------------------
@main_bp.route("/")
def index():
    conn = get_db_connection()

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    sort = request.args.get("sort", "")

    query = "SELECT * FROM cars WHERE 1=1"
    params = {}

    if search:
        query += " AND (title ILIKE %(search)s OR description ILIKE %(search)s)"
        params["search"] = f"%{search}%"

    if category:
        query += " AND category = %(category)s"
        params["category"] = category

    if min_price:
        query += " AND price >= %(min_price)s"
        params["min_price"] = float(min_price)

    if max_price:
        query += " AND price <= %(max_price)s"
        params["max_price"] = float(max_price)

    # Sorting
    if sort == "price_asc":
        query += " ORDER BY price ASC"
    elif sort == "price_desc":
        query += " ORDER BY price DESC"
    elif sort == "newest":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"

    cars = conn.execute(query, params).fetchall()
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
        sort=sort,
    )


# -------------------------------------------------
# BROWSE CARS PAGE (Search + Pagination + Sorting)
# -------------------------------------------------
@main_bp.route("/cars")
def cars():
    conn = get_db_connection()

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "date_added")
    page = int(request.args.get("page", 1))
    per_page = 6

    query = "SELECT * FROM cars WHERE 1=1"
    params = {}

    if search:
        query += " AND (title ILIKE %(search)s OR description ILIKE %(search)s)"
        params["search"] = f"%{search}%"

    if category:
        query += " AND category = %(category)s"
        params["category"] = category

    # Sorting
    if sort_by == "price":
        query += " ORDER BY price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY price DESC"
    elif sort_by == "title":
        query += " ORDER BY title ASC"
    else:
        query += " ORDER BY date_added DESC"

    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    cars = conn.execute(query, params).fetchall()

    # Count total
    count_query = "SELECT COUNT(*) FROM cars WHERE 1=1"
    count_params = {}

    if search:
        count_query += " AND (title ILIKE %(search)s OR description ILIKE %(search)s)"
        count_params["search"] = f"%{search}%"

    if category:
        count_query += " AND category = %(category)s"
        count_params["category"] = category

    total_cars = conn.execute(count_query, count_params).fetchone()[0]
    total_pages = (total_cars + per_page - 1) // per_page

    categories = [
        row["category"]
        for row in conn.execute(
            "SELECT DISTINCT category FROM cars WHERE category IS NOT NULL"
        ).fetchall()
    ]

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


# -------------------------------------------------
# CAR DETAILS PAGE
# -------------------------------------------------
@main_bp.route("/cars/<int:car_id>")
def car_detail(car_id):
    conn = get_db_connection()

    car = conn.execute("SELECT * FROM cars WHERE id = %(id)s", {"id": car_id}).fetchone()

    if not car:
        flash("Car not found.", "error")
        return redirect(url_for("main.cars"))

    seller = None
    if car["seller_id"]:
        seller = conn.execute(
            "SELECT * FROM sellers WHERE id = %(sid)s", {"sid": car["seller_id"]}
        ).fetchone()

    car_images = conn.execute(
        "SELECT * FROM car_images WHERE car_id = %(cid)s", {"cid": car_id}
    ).fetchall()

    conn.close()

    return render_template(
        "car_detail.html", car=car, seller=seller, car_images=car_images
    )


# -------------------------------------------------
# ADD CAR PAGE
# -------------------------------------------------
@main_bp.route("/add_car", methods=["GET", "POST"])
def add_car():
    conn = get_db_connection()
    sellers = conn.execute("SELECT * FROM sellers").fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        price = request.form.get("price", 0)
        category = request.form.get("category", "")
        seller_id = request.form.get("seller_id")
        mileage = request.form.get("mileage", "")
        body_condition = request.form.get("body_condition", "")
        fuel_efficiency = request.form.get("fuel_efficiency", "")
        engine_performance = request.form.get("engine_performance", "")

        # ---------------- Main Image -----------------
        main_image_file = request.files.get("main_image")
        main_image_path = None

        if main_image_file and main_image_file.filename:
            filename = secure_filename(main_image_file.filename)
            main_image_path = os.path.join(UPLOAD_FOLDER, filename)
            full_path = os.path.join(current_app.root_path, main_image_path)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            main_image_file.save(full_path)

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cars
            (title, description, price, category, seller_id, image, mileage, body_condition, fuel_efficiency, engine_performance)
            VALUES (%(title)s, %(description)s, %(price)s, %(category)s, %(seller_id)s, %(image)s,
            %(mileage)s, %(body_condition)s, %(fuel_efficiency)s, %(engine_performance)s)
            """,
            {
                "title": title,
                "description": description,
                "price": price,
                "category": category,
                "seller_id": seller_id,
                "image": "/" + main_image_path if main_image_path else None,
                "mileage": mileage,
                "body_condition": body_condition,
                "fuel_efficiency": fuel_efficiency,
                "engine_performance": engine_performance,
            },
        )

        car_id = cursor.lastrowid

        # ---------------- Additional Images -----------------
        files = request.files.getlist("images")

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                full_path = os.path.join(current_app.root_path, image_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

                cursor.execute(
                    """
                    INSERT INTO car_images (car_id, image_path)
                    VALUES (%(car_id)s, %(image_path)s)
                    """,
                    {"car_id": car_id, "image_path": "/" + image_path},
                )

        conn.commit()
        conn.close()

        flash("Car uploaded successfully!", "success")
        return redirect(url_for("main.cars"))

    conn.close()
    return render_template("add_car.html", sellers=sellers)


# -------------------------------------------------
# CONTACT SELLER FORM
# -------------------------------------------------
@main_bp.route("/contact_seller/<int:seller_id>", methods=["GET", "POST"])
def contact_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute(
        "SELECT * FROM sellers WHERE id = %(sid)s", {"sid": seller_id}
    ).fetchone()
    conn.close()

    if not seller:
        flash("Seller not found.", "error")
        return redirect(url_for("main.cars"))

    if request.method == "POST":
        flash(f"Message sent to {seller['name']} successfully!", "success")
        return redirect(url_for("main.cars"))

    return render_template("contact_seller.html", seller=seller)


# -------------------------------------------------
# SEND MESSAGE (Email + WhatsApp)
# -------------------------------------------------
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
        f"Email: {email}\n\n"
        f"{message}"
    )

    # -------- WhatsApp Redirect --------
    import urllib.parse

    wa_text = urllib.parse.quote(
        f"Hello {seller_name},\nYou have a new inquiry about *{car_title}*.\n\n"
        f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"
    )

    whatsapp_url = f"https://wa.me/{seller_phone}?text={wa_text}"

    # -------- Try sending email --------
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(full_message)
        msg["Subject"] = f"New Message About {car_title}"
        msg["From"] = email
        msg["To"] = seller_email

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login("YOUR_GMAIL", "YOUR_APP_PASSWORD")
        smtp.sendmail(email, seller_email, msg.as_string())
        smtp.quit()

    except Exception as e:
        print("Email error:", e)

    return redirect(whatsapp_url)
