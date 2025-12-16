import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)


# ---------------------------
# LOGIN ROUTE
# ---------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")

        conn = get_db_connection()
        # Use parameterized query to prevent SQL injection
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            # Store only necessary session info
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ---------------------------
# LOGOUT ROUTE
# ---------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("main.index"))


# ---------------------------
# REGISTER ROUTE
# ---------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Basic validation
        if not username or not password or not confirm:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        pw_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, pw_hash)
            )
            conn.commit()
            conn.close()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

    return render_template("register.html")
