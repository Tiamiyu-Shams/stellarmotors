import os
import urllib.parse
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    current_app
)
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor
from db import get_db_connection

main_bp = Blueprint("main", __name__)

# =========================================================
# HOME PAGE – SEARCH
# =========================================================
@main_bp.route("/")
def index():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    if search:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        like = f"%{search}%"
        params.extend([like, like])

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY id DESC"

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params)
    cars = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", cars=cars)


# =========================================================
# LIST CARS – SEARCH + SORT + PAGINATION
# =========================================================
@main_bp.route("/cars")
def cars():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "newest")
    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page - 1) * per_page

    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    if search:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        like = f"%{search}%"
        params.extend([like, like])

    if category:
        query += " AND category = %s"
        params.append(category)

    if sort_by == "price":
        query += " ORDER BY price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY price DESC"
    elif sort_by == "title":
        query += " ORDER BY title ASC"
    else:
        query += " ORDER BY id DESC"

    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cursor.execute(query, params)
    cars_data = cursor.fetchall()

    # Count for pagination
    count_query = "SELECT COUNT(*) FROM cars WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (title ILIKE %s OR description ILIKE %s)"
        count_params.extend([like, like])

    if category:
        count_query += " AND category = %s"
        count_params.append(category)

    cursor.execute(count_query, count_params)
    total = cursor.fetchone()["count"]
    total_pages = (total + per_page - 1) // per_page

    cursor.execute("SELECT DISTINCT category FROM cars WHERE category IS NOT NULL")
    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "cars.html",
        cars=cars_data,
        categories=categories,
        search=search,
        category=category,
        sort_by=sort_by,
        page=page,
        total_pages=total_pages,
    )


# =========================================================
# CAR DETAILS PAGE
# =========================================================
@main_bp.route("/cars/<int:car_id>")
def car_detail(car_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM cars WHERE id = %s", (car_id,))
    car = cursor.fetchone()

    if not car:
        cursor.close()
        conn.close()
        flash("Car not found.", "error")
        return redirect(url_for("main.cars"))

    seller = None
    if car.get("seller_id"):
        cursor.execute("SELECT * FROM sellers WHERE id = %s", (car["seller_id"],))
        seller = cursor.fetchone()

    cursor.execute("SELECT * FROM car_images WHERE car_id = %s", (car_id,))
    images = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("car_detail.html", car=car, seller=seller, car_images=images)


# =========================================================
# ADD CAR
# =========================================================
@main_bp.route("/add_car", methods=["GET", "POST"])
def add_car():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM sellers ORDER BY name ASC")
    sellers = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "")
        price = float(request.form.get("price", 0))
        category = request.form.get("category")
        seller_id = request.form.get("seller_id")
        mileage = request.form.get("mileage")
        body_condition = request.form.get("body_condition")
        fuel_efficiency = request.form.get("fuel_efficiency")
        engine_performance = request.form.get("engine_performance")

        # FILE UPLOAD
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        main_image = request.files.get("main_image")
        image_path = None

        if main_image and main_image.filename:
            filename = secure_filename(main_image.filename)
            image_path = os.path.join("static/uploads", filename)
            full_path = os.path.join(upload_folder, filename)
            os.makedirs(upload_folder, exist_ok=True)
            main_image.save(full_path)

        # SAVE CAR
        cursor.execute(
            """
            INSERT INTO cars
            (title, description, price, category, seller_id, image,
             mileage, body_condition, fuel_efficiency, engine_performance)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                title, description, price, category, seller_id, image_path,
                mileage, body_condition, fuel_efficiency, engine_performance
            ),
        )
        car_id = cursor.fetchone()["id"]

        # MULTIPLE EXTRA IMAGES
        for file in request.files.getlist("images"):
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join("static/uploads", filename)
                full = os.path.join(upload_folder, filename)
                file.save(full)

                cursor.execute(
                    "INSERT INTO car_images (car_id, image_path) VALUES (%s,%s)",
                    (car_id, path),
                )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Car added successfully", "success")
        return redirect(url_for("main.cars"))

    cursor.close()
    conn.close()
    return render_template("add_car.html", sellers=sellers)


# =========================================================
# CONTACT SELLER
# =========================================================
@main_bp.route("/contact_seller/<int:seller_id>", methods=["GET", "POST"])
def contact_seller(seller_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM sellers WHERE id = %s", (seller_id,))
    seller = cursor.fetchone()

    cursor.close()
    conn.close()

    if not seller:
        flash("Seller not found.", "error")
        return redirect(url_for("main.cars"))

    if request.method == "POST":
        flash(f"Message sent to {seller['name']}", "success")
        return redirect(url_for("main.cars"))

    return render_template("contact_seller.html", seller=seller)


# =========================================================
# SEND MESSAGE (EMAIL + WHATSAPP)
# =========================================================
@main_bp.route("/send_message", methods=["POST"])
def send_message():
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]
    seller_phone = request.form["seller_phone"]
    seller_email = request.form["seller_email"]
    seller_name = request.form["seller_name"]
    car_title = request.form["car_title"]

    wa_text = urllib.parse.quote(
        f"Hello {seller_name},\n\n"
        f"New inquiry about *{car_title}*\n\n"
        f"From: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}"
    )
    whatsapp_url = f"https://wa.me/{seller_phone}?text={wa_text}"

    # EMAIL
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(message)
        msg["Subject"] = f"New inquiry: {car_title}"
        msg["From"] = email
        msg["To"] = seller_email

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )
        smtp.sendmail(email, seller_email, msg.as_string())
        smtp.quit()
    except Exception as e:
        print("Email error:", e)

    return redirect(whatsapp_url)
