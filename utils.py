import os
from werkzeug.utils import secure_filename
from flask import url_for
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_upload(file, default_path):
    """
    Save uploaded file to UPLOAD_FOLDER and return a static URL.
    - call this inside a view (request/context available).
    - default_path is returned if no valid upload.
    """
    if not file or file.filename == "":
        return default_path

    if allowed_file(file.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        return url_for("static", filename=f"uploads/{filename}")
    return default_path
