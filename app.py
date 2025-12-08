import os
from flask import Flask
from flask_mail import Mail

from config import SECRET_KEY, UPLOAD_FOLDER

# -------------------------------
# AUTO-SELECT DATABASE BACKEND
# -------------------------------
if os.getenv("RENDER") or os.getenv("DATABASE_URL"):
    from db_render import init_db, seed_data, get_db_connection
    print("🔗 Connected to: Render PostgreSQL (db_render.py)")
else:
    from db_local import init_db, seed_data, get_db_connection
    print("🗄 Using Local SQLite (db_local.py)")


# -------------------------------------
# BLUEPRINTS
# -------------------------------------
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp


mail = Mail()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # -------------------------------------
    # UPLOADS CONFIG
    # -------------------------------------
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # -------------------------------------
    # MAIL CONFIG (GMAIL)
    # -------------------------------------
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "your_email@gmail.com"
    app.config["MAIL_PASSWORD"] = "your_app_password"

    mail.init_app(app)

    # -------------------------------------
    # REGISTER ROUTES
    # -------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # -------------------------------------
    # DATABASE SETUP
    # -------------------------------------
    print("📦 Initializing Database...")
    init_db()
    seed_data()

    return app


# Run app locally
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
