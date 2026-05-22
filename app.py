from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)

app.secret_key = "habit_tracker_secret_key"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init-db")
def initialize_database():
    init_db()
    return "Database initialized successfully!"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            connection.commit()
        except:
            flash("Username or email already exists.")
            connection.close()
            return redirect(url_for("register"))

        connection.close()
        flash("Account created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        connection = get_db_connection()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        connection.close()

        if user is None:
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        if not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    connection = get_db_connection()
    habits = connection.execute(
        """
        SELECT * FROM habits
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()
    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        habits=habits
    )

@app.route("/add-habit", methods=["GET", "POST"])
def add_habit():
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        frequency = request.form["frequency"]

        if not title:
            flash("Habit title is required.")
            return redirect(url_for("add_habit"))

        connection = get_db_connection()
        connection.execute(
            """
            INSERT INTO habits (user_id, title, description, frequency)
            VALUES (?, ?, ?, ?)
            """,
            (session["user_id"], title, description, frequency)
        )
        connection.commit()
        connection.close()

        flash("Habit added successfully.")
        return redirect(url_for("dashboard"))

    return render_template("add_habit.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)