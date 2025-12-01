from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db_connection
from utils import handle_upload
from werkzeug.utils import secure_filename
import os
from flask import current_app

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
def dashboard():
    if not session.get("user_id"):
        flash("Please log in to access admin.", "info")
        return redirect(url_for("auth.login"))
    conn = get_db_connection()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", cars=cars, username=session.get("username"))

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
    image_url = handle_upload(request.files.get("image"), request.form.get("current_image") or "/static/images/default_car.jpg")
    seller_url = handle_upload(request.files.get("seller_photo"), request.form.get("current_seller_photo") or "/static/images/default_seller.jpg")
    seller_name = request.form.get("seller_name", "").strip()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO cars (title, description, price, image, seller_name, seller_photo, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, description, price, image_url, seller_name, seller_url, category)
    )
    conn.commit()
    conn.close()
    flash("✅ Car added successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/edit_car/<int:car_id>", methods=["GET", "POST"])
def edit_car(car_id):
    if not session.get("user_id"):
        flash("Please log in.", "info")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        # Price stays numeric
        price = float(request.form.get("price", "0") or 0)

        # New fields
        mileage = request.form.get("mileage", "").strip() or None
        body_condition = request.form.get("body_condition", "").strip() or None
        fuel_efficiency = request.form.get("fuel_efficiency", "").strip() or None
        engine_performance = request.form.get("engine_performance", "").strip() or None

        category = request.form.get("category", "").strip() or None

        # Images
        image_url = handle_upload(request.files.get("image"), request.form.get("current_image"))
        seller_url = handle_upload(request.files.get("seller_photo"), request.form.get("current_seller_photo"))

        # Seller backward support (still supported but will phase out)
        seller_name = request.form.get("seller_name", "").strip()

        conn.execute("""
            UPDATE cars
            SET title=?, description=?, price=?, image=?, seller_name=?, seller_photo=?, category=?,
                mileage=?, body_condition=?, fuel_efficiency=?, engine_performance=?
            WHERE id=?
        """, (
            title, description, price, image_url, seller_name, seller_url, category,
            mileage, body_condition, fuel_efficiency, engine_performance,
            car_id
        ))

        conn.commit()
        conn.close()

        flash("✅ Car updated successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    # GET request (load car data)
    car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    conn.close()

    if not car:
        flash("Car not found.", "error")
        return redirect(url_for("admin.dashboard"))

    return render_template("edit_car.html", car=car)
    


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




@admin_bp.route("/add_seller", methods=["GET", "POST"])
def add_seller():
    if request.method == "POST":
        name = request.form["name"]
        contact_email = request.form["contact_email"]
        phone = request.form["phone"]
        address = request.form["address"]
        about = request.form["about"]

        # Handle photo upload
        photo = request.files["photo"]
        photo_filename = "default_seller.PNG"  # default

        upload_folder = os.path.join("static", "uploads", "sellers")
        os.makedirs(upload_folder, exist_ok=True)  # ✅ Create folder if missing

        if photo and photo.filename != "":
            photo_filename = photo.filename
            photo.save(os.path.join(upload_folder, photo_filename))



        # Insert into DB
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO sellers (name, contact_email, phone, address, about, photo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, contact_email, phone, address, about, photo_filename))
        conn.commit()
        conn.close()

        flash("Seller added successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("add_seller.html")



# --- ADMIN: LIST SELLERS WITH SEARCH & SORT ---
@admin_bp.route("/sellers")
def sellers():
    conn = get_db_connection()

    # Get search and sort parameters from the query string
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "id")  # changed to match HTML form
    order = request.args.get("order", "asc")

    # Base query
    query = "SELECT * FROM sellers"
    params = []

    # Add search filter if provided
    if search:
        query += " WHERE name LIKE ? OR contact_email LIKE ? OR phone LIKE ?"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    # Validate and apply sorting field
    valid_sort_fields = ["id", "name", "contact_email", "phone"]
    if sort_by not in valid_sort_fields:
        sort_by = "id"

    # Validate sort order
    if order.lower() not in ["asc", "desc"]:
        order = "asc"

    # Finalize query
    query += f" ORDER BY {sort_by} {order.upper()}"

    # Execute and fetch results
    sellers = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "seller_list.html",
        sellers=sellers,
        search=search,
        sort_by=sort_by,
        order=order
    )



# --- EDIT SELLER ---
@admin_bp.route("/edit_seller/<int:seller_id>", methods=["GET", "POST"])
def edit_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute("SELECT * FROM sellers WHERE id = ?", (seller_id,)).fetchone()

    if not seller:
        conn.close()
        flash("Seller not found.", "danger")
        return redirect(url_for("admin.sellers"))

    if request.method == "POST":
        name = request.form["name"]
        contact_email = request.form["contact_email"]
        phone = request.form["phone"]
        address = request.form.get("address", "")
        about = request.form.get("about", "")
        photo = request.files.get("photo")

        photo_filename = seller["photo"]  # keep existing photo by default
        if photo and photo.filename:
            upload_dir = os.path.join("static", "uploads", "sellers")
            os.makedirs(upload_dir, exist_ok=True)
            photo_filename = photo.filename
            photo.save(os.path.join(upload_dir, photo_filename))

        conn.execute(
            """
            UPDATE sellers 
            SET name = ?, contact_email = ?, phone = ?, address = ?, about = ?, photo = ?
            WHERE id = ?
            """,
            (name, contact_email, phone, address, about, photo_filename, seller_id),
        )
        conn.commit()
        conn.close()

        flash("Seller details updated successfully!", "success")
        return redirect(url_for("admin.sellers"))

    conn.close()
    return render_template("edit_seller.html", seller=seller)


# --- DELETE SELLER ---
@admin_bp.route("/delete_seller/<int:seller_id>")
def delete_seller(seller_id):
    conn = get_db_connection()
    seller = conn.execute("SELECT * FROM sellers WHERE id = ?", (seller_id,)).fetchone()

    if not seller:
        conn.close()
        flash("Seller not found.", "danger")
        return redirect(url_for("admin.sellers"))

    # Optionally delete seller photo
    if seller["photo"]:
        photo_path = os.path.join("static", "uploads", "sellers", seller["photo"])
        if os.path.exists(photo_path):
            os.remove(photo_path)

    conn.execute("DELETE FROM sellers WHERE id = ?", (seller_id,))
    conn.commit()
    conn.close()

    flash("Seller deleted successfully.", "success")
    return redirect(url_for("admin.sellers"))



# --- ADMIN: LIST CARS WITH SEARCH & SORT ---
@admin_bp.route("/cars")
def cars():
    conn = get_db_connection()

    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "id")
    order = request.args.get("order", "asc")

    # Build SQL query dynamically
    query = "SELECT * FROM cars"
    params = []

    if search:
        query += " WHERE name LIKE ? OR type LIKE ? OR price LIKE ?"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if sort_by not in ["id", "name", "type", "price"]:
        sort_by = "id"

    query += f" ORDER BY {sort_by} {order.upper()}"

    cars = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("admin_cars.html", cars=cars, search=search, sort_by=sort_by, order=order)
