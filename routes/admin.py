import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from db import get_db_connection
from utils import handle_upload

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------------------
# DASHBOARD
# ---------------------------
@admin_bp.route("/")
def dashboard():
    if not session.get("user_id"):
        flash("Please log in to access admin.", "info")
        return redirect(url_for("auth.login"))
    conn = get_db_connection()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", cars=cars, username=session.get("username"))


# ---------------------------
# ADD CAR
# ---------------------------
@admin_bp.route("/add_car", methods=["POST"])
def add_car():
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    price_raw = request.form.get("price", "0").replace(",", "")
    price = float(price_raw or 0)

    category = request.form.get("category", "").strip() or None
    image_url = handle_upload(
        request.files.get("image"),
        request.form.get("current_image") or "/static/images/default_car.jpg"
    )
    seller_url = handle_upload(
        request.files.get("seller_photo"),
        request.form.get("current_seller_photo") or "/static/images/default_seller.jpg"
    )
    seller_name = request.form.get("seller_name", "").strip()

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO cars
        (title, description, price, image, seller_name, seller_photo, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, price, image_url, seller_name, seller_url, category)
    )
    conn.commit()
    conn.close()
    flash("✅ Car added successfully.", "success")
    return redirect(url_for("admin.dashboard"))


# ---------------------------
# EDIT CAR
# ---------------------------
@admin_bp.route("/edit_car/<int:car_id>", methods=["GET", "POST"])
def edit_car(car_id):
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()

    if not car:
        conn.close()
        flash("Car not found.", "error")
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = float(request.form.get("price", "0") or 0)
        mileage = request.form.get("mileage", "").strip() or None
        body_condition = request.form.get("body_condition", "").strip() or None
        fuel_efficiency = request.form.get("fuel_efficiency", "").strip() or None
        engine_performance = request.form.get("engine_performance", "").strip() or None
        category = request.form.get("category", "").strip() or None

        image_url = handle_upload(request.files.get("image"), request.form.get("current_image"))
        seller_url = handle_upload(request.files.get("seller_photo"), request.form.get("current_seller_photo"))
        seller_name = request.form.get("seller_name", "").strip()

        conn.execute(
            """
            UPDATE cars
            SET title=?, description=?, price=?, image=?, seller_name=?, seller_photo=?, category=?,
                mileage=?, body_condition=?, fuel_efficiency=?, engine_performance=?
            WHERE id=?
            """,
            (
                title, description, price, image_url, seller_name, seller_url, category,
                mileage, body_condition, fuel_efficiency, engine_performance,
                car_id
            )
        )
        conn.commit()
        conn.close()
        flash("✅ Car updated successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    conn.close()
    return render_template("edit_car.html", car=car)


# ---------------------------
# DELETE CAR
# ---------------------------
@admin_bp.route("/delete_car/<int:car_id>")
def delete_car(car_id):
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    flash("🗑️ Car deleted.", "success")
    return redirect(url_for("admin.dashboard"))


# ---------------------------
# ADD SELLER
# ---------------------------
@admin_bp.route("/add_seller", methods=["GET", "POST"])
def add_seller():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        about = request.form.get("about", "").strip()

        photo = request.files.get("photo")
        upload_folder = os.path.join("static", "uploads", "sellers")
        os.makedirs(upload_folder, exist_ok=True)

        photo_filename = "default_seller.PNG"
        if photo and photo.filename:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(upload_folder, photo_filename))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO sellers (name, contact_email, phone, address, about, photo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, contact_email, phone, address, about, photo_filename)
        )
        conn.commit()
        conn.close()
        flash("Seller added successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("add_seller.html")


# ---------------------------
# LIST SELLERS
# ---------------------------
@admin_bp.route("/sellers")
def sellers():
    conn = get_db_connection()
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "asc").lower()

    if order not in ["asc", "desc"]:
        order = "asc"

    valid_fields = ["id", "name", "contact_email", "phone"]
    if sort_by not in valid_fields:
        sort_by = "id"

    query = "SELECT * FROM sellers"
    params = []
    if search:
        query += " WHERE name LIKE ? OR contact_email LIKE ? OR phone LIKE ?"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += f" ORDER BY {sort_by} {order.upper()}"
    sellers_list = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("seller_list.html", sellers=sellers_list, search=search, sort_by=sort_by, order=order)


# ---------------------------
# EDIT SELLER
# ---------------------------
@admin_bp.route("/edit_seller/<int:seller_id>", methods=["GET", "POST"])
def edit_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute("SELECT * FROM sellers WHERE id=?", (seller_id,)).fetchone()

    if not seller:
        conn.close()
        flash("Seller not found.", "danger")
        return redirect(url_for("admin.sellers"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        about = request.form.get("about", "").strip()
        photo = request.files.get("photo")

        photo_filename = seller["photo"]
        if photo and photo.filename:
            upload_dir = os.path.join("static", "uploads", "sellers")
            os.makedirs(upload_dir, exist_ok=True)
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(upload_dir, photo_filename))

        conn.execute(
            """
            UPDATE sellers
            SET name=?, contact_email=?, phone=?, address=?, about=?, photo=?
            WHERE id=?
            """,
            (name, contact_email, phone, address, about, photo_filename, seller_id)
        )
        conn.commit()
        conn.close()
        flash("Seller details updated successfully!", "success")
        return redirect(url_for("admin.sellers"))

    conn.close()
    return render_template("edit_seller.html", seller=seller)


# ---------------------------
# DELETE SELLER
# ---------------------------
@admin_bp.route("/delete_seller/<int:seller_id>")
def delete_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute("SELECT * FROM sellers WHERE id=?", (seller_id,)).fetchone()

    if not seller:
        conn.close()
        flash("Seller not found.", "danger")
        return redirect(url_for("admin.sellers"))

    # Delete photo if exists
    if seller["photo"]:
        photo_path = os.path.join("static", "uploads", "sellers", seller["photo"])
        if os.path.exists(photo_path):
            os.remove(photo_path)

    conn.execute("DELETE FROM sellers WHERE id=?", (seller_id,))
    conn.commit()
    conn.close()
    flash("Seller deleted successfully.", "success")
    return redirect(url_for("admin.sellers"))
