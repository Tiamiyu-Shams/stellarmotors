from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor
import os

from db import get_db_connection
from utils import handle_upload, handle_multi_upload


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------------------
@admin_bp.route("/")
def dashboard():
    if not session.get("user_id"):
        flash("Please log in to access admin.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM cars ORDER BY id DESC")
    cars = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "admin.html",
        username=session.get("username"),
        cars=cars
    )


# ------------------------------------------------------------
# ADD SELLER (FORM PAGE)
# ------------------------------------------------------------
@admin_bp.route("/add_seller", methods=["GET"])
def add_seller_page():
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    return render_template("add_seller.html")


# ------------------------------------------------------------
# ADD SELLER (SUBMIT)
# ------------------------------------------------------------
@admin_bp.route("/add_seller", methods=["POST"])
def add_seller():
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    form = request.form
    files = request.files

    name = form.get("name")
    email = form.get("contact_email")
    phone = form.get("phone")
    address = form.get("address")
    about = form.get("about")

    photo = handle_upload(
        files.get("photo"),
        "/static/images/default_seller.jpg"
    )

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sellers
            (name, contact_email, phone, address, about, photo)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (name, email, phone, address, about, photo)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Seller added successfully!", "success")
    return redirect(url_for("admin.sellers"))


# ------------------------------------------------------------
# SELLERS LIST PAGE
# ------------------------------------------------------------
@admin_bp.route("/sellers")
def sellers():
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM sellers ORDER BY id DESC")
    sellers = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin_sellers.html", sellers=sellers)


# ------------------------------------------------------------
# ADD CAR (FORM PAGE)
# ------------------------------------------------------------
@admin_bp.route("/add_car", methods=["GET"])
def add_car_page():
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, name FROM sellers ORDER BY name ASC")
    sellers = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("add_car.html", sellers=sellers)


# ------------------------------------------------------------
# ADD CAR (SUBMIT)
# ------------------------------------------------------------
@admin_bp.route("/add_car", methods=["POST"])
def add_car():
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    form = request.form
    files = request.files

    title = form.get("title")
    description = form.get("description")
    price = float(form.get("price") or 0)
    category = form.get("category") or None
    mileage = form.get("mileage")
    body_condition = form.get("body_condition")
    fuel_efficiency = form.get("fuel_efficiency")
    engine_performance = form.get("engine_performance")
    seller_id = form.get("seller_id")

    main_image = handle_upload(
        files.get("main_image"),
        "/static/images/default_car.jpg"
    )

    images = handle_multi_upload(files.getlist("images"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cars (
            title, description, price, category, mileage, body_condition,
            fuel_efficiency, engine_performance, seller_id, main_image
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            title, description, price, category, mileage, body_condition,
            fuel_efficiency, engine_performance, seller_id, main_image
        )
    )
    conn.commit()

    # new row id
    cur.execute("SELECT LASTVAL()")
    car_id = cur.fetchone()[0]

    if images:
        cur.executemany(
            "INSERT INTO car_images (car_id, image_url) VALUES (%s, %s)",
            [(car_id, img) for img in images]
        )

    conn.commit()
    cur.close()
    conn.close()

    flash("Car uploaded successfully!", "success")
    return redirect(url_for("admin.dashboard"))


# ------------------------------------------------------------
# DELETE CAR
# ------------------------------------------------------------
@admin_bp.route("/delete_car/<int:car_id>")
def delete_car(car_id):
    if not session.get("user_id"):
        flash("Login required.", "warning")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM car_images WHERE car_id=%s", (car_id,))
    cur.execute("DELETE FROM cars WHERE id=%s", (car_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Car deleted.", "info")
    return redirect(url_for("admin.dashboard"))


# ------------------------------------------------------------
# PLACEHOLDER: EDIT CAR
# ------------------------------------------------------------
@admin_bp.route("/edit_car/<int:car_id>")
def edit_car(car_id):
    flash("Edit page coming soon.", "info")
    return redirect(url_for("admin.dashboard"))
