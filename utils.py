import os
from werkzeug.utils import secure_filename
from flask import url_for
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS


def allowed_file(filename: str) -> bool:
    """
    Checks if a filename has an allowed extension.
    """
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file_obj):
    """
    Saves one Werkzeug `FileStorage` object to disk and returns the stored filename.
    """
    filename = secure_filename(file_obj.filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(path)
    return filename


def handle_upload(file_obj, default_path: str):
    """
    Handles a **single uploaded file** and returns a STATIC URL.
    - If file invalid → return default_path
    - If valid → save & return `/static/uploads/<file>`
    """
    if not file_obj or file_obj.filename.strip() == "":
        return default_path

    if not allowed_file(file_obj.filename):
        return default_path

    filename = save_file(file_obj)
    return url_for("static", filename=f"uploads/{filename}")


def handle_multi_upload(file_list):
    """
    Handles **multiple uploaded files**.
    - Accepts a list of Werkzeug `FileStorage` objects.
    - Returns a list of STATIC URLs.
    - Ignores invalid or empty uploads.
    """
    stored_urls = []

    if not file_list:
        return stored_urls

    for file_obj in file_list:
        if file_obj and file_obj.filename and allowed_file(file_obj.filename):
            filename = save_file(file_obj)
            url = url_for("static", filename=f"uploads/{filename}")
            stored_urls.append(url)

    return stored_urls
