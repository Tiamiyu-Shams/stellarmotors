from flask import Flask, render_template, request, redirect, url_for, flash
import os

# choose correct DB engine
if os.environ.get("RENDER"):
    from db_render import get_db
else:
    from db_local import get_db

app = Flask(__name__)  # <<< THIS MUST EXIST
app.secret_key = "replace-this"

# --- HOME PAGE ---
@app.route("/")
def home():
    db = get_db()
    cars = db.execute("SELECT * FROM cars").fetchall()
    return render_template("index.html", cars=cars)

# --- ADD CAR ---
@app.route("/add", methods=["GET", "POST"])
def add_car():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        db = get_db()
        db.execute("INSERT INTO cars (name, price) VALUES (?, ?)", (name, price))
        db.commit()
        flash("Car added successfully")
        return redirect(url_for("home"))

    return render_template("add.html")


if __name__ == "__main__":
    app.run(debug=True)
