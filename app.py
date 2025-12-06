from flask import Flask
from config import SECRET_KEY, UPLOAD_FOLDER
import os
from werkzeug.utils import secure_filename

# import DB helpers to initialize DB on first run
from db import init_db, seed_data

# import DB helpers
from flask_mail import Mail  # NEW IMPORT

# blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp

mail = Mail()  # create mail object globally


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # uploads
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


    # -----------------------------
    # MAIL CONFIGURATION (ADD THIS)
    # -----------------------------
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "your_email@gmail.com"
    app.config["MAIL_PASSWORD"] = "your_app_password"

    mail.init_app(app)  # initialize mail


    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # init DB & seed
    init_db()
    seed_data()

    return app

app = create_app()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

