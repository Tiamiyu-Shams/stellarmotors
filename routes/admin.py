from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor
import os

from db import get_db_connection
from utils import handle_upload

# --------------------------------
# BLUEPRINT
# --------------------------------
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------
# DASHBOARD
# --------------------------------
@admin_bp.route("/")
def dashboard():
    if not session.get("user_id"):
        flash("Please log in to access admin.", "info")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM cars ORDER BY id DESC")
    cars = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        cars=cars,
        username=session.get("username")
    )


# --------------------------------
# ADD SELLER (FIXES YOUR ERROR)
# --------------------------------
@admin_bp.route("/add_seller", methods=["GET", "POST"])
def add_seller():
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        photo = handle_upload(
            request.files.get("photo"),
            "/static/images/default_seller.jpg"
        )

        if not name:
            flash("Seller name is required.", "error")
            return redirect(url_for("admin.add_seller"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sellers (name, phone, email, photo)
            VALUES (%s, %s, %s, %s)
            """,
            (name, phone, email, photo)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Seller added successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("add_seller.html")


# --------------------------------
# ADD CAR
# --------------------------------
@admin_bp.route("/add_car", methods=["POST"])
def add_car():
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    price = float(request.form.get("price", "0").replace(",", "") or 0)
    category = request.form.get("category") or None
    seller_name = request.form.get("seller_name", "").strip()

    image_url = handle_upload(
        request.files.get("image"),
        "/static/images/default_car.jpg"
    )

    seller_photo = handle_upload(
        request.files.get("seller_photo"),
        "/static/images/default_seller.jpg"
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO cars (title, description, price, image, seller_name, seller_photo, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (title, description, price, image_url, seller_name, seller_photo, category)
    )

    conn.commit()
    cursor.close()
    conn.close()

    flash("Car added successfully.", "success")
    return redirect(url_for("admin.dashboard"))
