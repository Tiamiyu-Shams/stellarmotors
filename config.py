
# single source of truth for DB and uploads
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# SECRET KEY (ENV ON PRODUCTION)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# UPLOAD PATH
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

# DATABASE URL (Render uses ENV)
DATABASE_URL = os.environ.get("DATABASE_URL")

# MAIL (ENV ON RENDER)
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

# Allowed Extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


