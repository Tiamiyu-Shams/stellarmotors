import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# single source of truth for DB and uploads
DB_NAME = os.path.join(BASE_DIR, "cars.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

# keep this in env in production; default is convenient for dev/demo
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey-change-me")

# allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
