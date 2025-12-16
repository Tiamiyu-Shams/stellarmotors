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
from db import get_db_connection

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
UPLOAD_FOLDER = "static/uploads"

main_bp = Blueprint("main", __name__)

# --------------------------------------------------
# HOME PAGE – FILTER + SORT
# --------------------------------------------------
@main_bp.route("/")
def index():
    conn = get_db_connection()

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    sort = request.args.get("sort", "newest")

    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    if category:
        query += " AND category = ?"
        params.append(category)

    if min_price:
        query += " AND price >= ?"
        params.append(float(min_price))

    if max_price:
        query += " AND price <= ?"
        params.append(float(max_price))

    if sort == "price_asc":
        query += " ORDER BY price ASC"
    elif sort == "price_desc":
        query += " ORDER BY price DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    else:
        query += " ORDER BY id DESC"

    cars = conn.execute(query, params).fetchall()
    categories = conn.execute(
        "SELECT DISTINCT category FROM cars WHERE category IS NOT NULL"
    ).fetchall()

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

# --------------------------------------------------
# LIST CARS – SEARCH + SORT + PAGINATION
# --------------------------------------------------
@main_bp.route("/cars")
def cars():
    conn = get_db_connection()

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "newest")
    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page - 1) * per_page

    query = "SELECT * FROM cars WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    if category:
        query += " AND category = ?"
        params.append(category)

    if sort_by == "price":
        query += " ORDER BY price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY price DESC"
    elif sort_by == "title":
        query += " ORDER BY title COLLATE NOCASE"
    else:
        query += " ORDER BY id DESC"

    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    cars = conn.execute(query, params).fetchall()

    count_query = "SELECT COUNT(*) FROM cars WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (title LIKE ? OR description LIKE ?)"
        count_params.extend([like, like])

    if category:
        count_query += " AND category = ?"
        count_params.append(category)

    total = conn.execute(count_query, count_params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page

    categories = conn.execute(
        "SELECT DISTINCT category FROM cars WHERE category IS NOT NULL"
    ).fetchall()

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

# --------------------------------------------------
# CAR DETAILS
# --------------------------------------------------
@main_bp.route("/cars/<int:car_id>")
def car_detail(car_id):
    conn = get_db_connection()

    car = conn.execute(
        "SELECT * FROM cars WHERE id = ?", (car_id,)
    ).fetchone()

    if not car:
        conn.close()
        flash("Car not found.", "error")
        return redirect(url_for("main.cars"))

    seller = None
    if car["seller_id"]:
        seller = conn.execute(
            "SELECT * FROM sellers WHERE id = ?", (car["seller_id"],)
        ).fetchone()

    images = conn.execute(
        "SELECT * FROM car_images WHERE car_id = ?", (car_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "car_detail.html",
        car=car,
        seller=seller,
        car_images=images,
    )

# --------------------------------------------------
# ADD CAR
# --------------------------------------------------
@main_bp.route("/add_car", methods=["GET", "POST"])
def add_car():
    conn = get_db_connection()
    sellers = conn.execute("SELECT * FROM sellers").fetchall()

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

        main_image = request.files.get("main_image")
        image_path = None

        if main_image and main_image.filename:
            filename = secure_filename(main_image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            full_path = os.path.join(current_app.root_path, image_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            main_image.save(full_path)
            image_path = "/" + image_path

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cars
            (title, description, price, category, seller_id, image,
             mileage, body_condition, fuel_efficiency, engine_performance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                price,
                category,
                seller_id,
                image_path,
                mileage,
                body_condition,
                fuel_efficiency,
                engine_performance,
            ),
        )

        car_id = cursor.lastrowid

        for file in request.files.getlist("images"):
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                full_path = os.path.join(current_app.root_path, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

                cursor.execute(
                    "INSERT INTO car_images (car_id, image_path) VALUES (?, ?)",
                    (car_id, "/" + path),
                )

        conn.commit()
        conn.close()

        flash("Car added successfully.", "success")
        return redirect(url_for("main.cars"))

    conn.close()
    return render_template("add_car.html", sellers=sellers)

# --------------------------------------------------
# CONTACT SELLER
# --------------------------------------------------
@main_bp.route("/contact_seller/<int:seller_id>", methods=["GET", "POST"])
def contact_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute(
        "SELECT * FROM sellers WHERE id = ?", (seller_id,)
    ).fetchone()
    conn.close()

    if not seller:
        flash("Seller not found.", "error")
        return redirect(url_for("main.cars"))

    if request.method == "POST":
        flash(f"Message sent to {seller['name']}!", "success")
        return redirect(url_for("main.cars"))

    return render_template("contact_seller.html", seller=seller)

# --------------------------------------------------
# SEND MESSAGE (EMAIL + WHATSAPP)
# --------------------------------------------------
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
            current_app.config["MAIL_PASSWORD"],
        )
        smtp.sendmail(email, seller_email, msg.as_string())
        smtp.quit()
    except Exception as e:
        print("Email error:", e)

    return redirect(whatsapp_url)
