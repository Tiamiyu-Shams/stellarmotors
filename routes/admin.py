from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import os

from db import get_db_connection
from utils import handle_upload

# --------------------------------
# BLUEPRINT DEFINITION (MUST BE FIRST)
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
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin.html", cars=cars, username=session.get("username"))


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
        request.form.get("current_image") or "/static/images/default_car.jpg"
    )

    seller_photo = handle_upload(
        request.files.get("seller_photo"),
        request.form.get("current_seller_photo") or "/static/images/default_seller.jpg"
    )

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO cars (title, description, price, image, seller_name, seller_photo, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, price, image_url, seller_name, seller_photo, category)
    )
    conn.commit()
    conn.close()

    flash("Car added successfully.", "success")
    return redirect(url_for("admin.dashboard"))
