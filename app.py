from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from business_logic import calculate_streak, calculate_weekly_progress

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

    search_query = request.args.get("search", "").strip()

    connection = get_db_connection()

    if search_query:
        habits = connection.execute(
            """
            SELECT 
                habits.*,
                CASE 
                    WHEN habit_logs.id IS NOT NULL THEN 1
                    ELSE 0
                END AS completed_today,
                CAST(julianday('now') - julianday(habits.created_at) AS INTEGER) + 1 AS active_days
            FROM habits
            LEFT JOIN habit_logs
                ON habits.id = habit_logs.habit_id
                AND habit_logs.completed_date = DATE('now')
            WHERE habits.user_id = ?
            AND habits.title LIKE ?
            ORDER BY habits.created_at DESC
            """,
            (session["user_id"], f"%{search_query}%")
        ).fetchall()
    else:
        habits = connection.execute(
            """
            SELECT 
                habits.*,
                CASE 
                    WHEN habit_logs.id IS NOT NULL THEN 1
                    ELSE 0
                END AS completed_today,
                CAST(julianday('now') - julianday(habits.created_at) AS INTEGER) + 1 AS active_days
            FROM habits
            LEFT JOIN habit_logs
                ON habits.id = habit_logs.habit_id
                AND habit_logs.completed_date = DATE('now')
            WHERE habits.user_id = ?
            ORDER BY habits.created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    habit_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM habits
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()["total"]

    completed_today_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM habit_logs
        WHERE user_id = ?
        AND completed_date = DATE('now')
        """,
        (session["user_id"],)
    ).fetchone()["total"]

    not_completed_today_count = habit_count - completed_today_count

    weekly_completed = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM habit_logs
        WHERE user_id = ?
        AND completed_date >= DATE('now', '-6 days')
        """,
        (session["user_id"],)
    ).fetchone()["total"]

    weekly_progress = calculate_weekly_progress(weekly_completed, habit_count)

    habits_with_streaks = []

    for habit in habits:
        logs = connection.execute(
            """
            SELECT completed_date
            FROM habit_logs
            WHERE habit_id = ? AND user_id = ?
            ORDER BY completed_date DESC
            """,
            (habit["id"], session["user_id"])
        ).fetchall()

        completed_dates = [log["completed_date"] for log in logs]
        streak = calculate_streak(completed_dates)

        habit_data = dict(habit)
        habit_data["streak"] = streak
        habits_with_streaks.append(habit_data)

    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        habits=habits_with_streaks,
        weekly_completed=weekly_completed,
        weekly_progress=weekly_progress,
        habit_count=habit_count,
        completed_today_count=completed_today_count,
        not_completed_today_count=not_completed_today_count,
        search_query=search_query
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

@app.route("/complete-habit/<int:habit_id>", methods=["POST"])
def complete_habit(habit_id):
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    connection = get_db_connection()

    habit = connection.execute(
        """
        SELECT * FROM habits
        WHERE id = ? AND user_id = ?
        """,
        (habit_id, session["user_id"])
    ).fetchone()

    if habit is None:
        connection.close()
        flash("Habit not found or access denied.")
        return redirect(url_for("dashboard"))

    try:
        connection.execute(
            """
            INSERT INTO habit_logs (habit_id, user_id, completed_date)
            VALUES (?, ?, DATE('now'))
            """,
            (habit_id, session["user_id"])
        )
        connection.commit()
        flash("Habit marked as completed for today.")
    except:
        flash("This habit is already completed today.")

    connection.close()
    return redirect(url_for("dashboard"))

@app.route("/edit-habit/<int:habit_id>", methods=["GET", "POST"])
def edit_habit(habit_id):
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    connection = get_db_connection()

    habit = connection.execute(
        """
        SELECT * FROM habits
        WHERE id = ? AND user_id = ?
        """,
        (habit_id, session["user_id"])
    ).fetchone()

    if habit is None:
        connection.close()
        flash("Habit not found or access denied.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        frequency = request.form["frequency"]

        if not title:
            flash("Habit title is required.")
            connection.close()
            return redirect(url_for("edit_habit", habit_id=habit_id))

        connection.execute(
            """
            UPDATE habits
            SET title = ?, description = ?, frequency = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, description, frequency, habit_id, session["user_id"])
        )
        connection.commit()
        connection.close()

        flash("Habit updated successfully.")
        return redirect(url_for("dashboard"))

    connection.close()
    return render_template("edit_habit.html", habit=habit)
@app.route("/delete-habit/<int:habit_id>", methods=["POST"])
def delete_habit(habit_id):
    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    connection = get_db_connection()

    habit = connection.execute(
        """
        SELECT * FROM habits
        WHERE id = ? AND user_id = ?
        """,
        (habit_id, session["user_id"])
    ).fetchone()

    if habit is None:
        connection.close()
        flash("Habit not found or access denied.")
        return redirect(url_for("dashboard"))

    connection.execute(
        """
        DELETE FROM habit_logs
        WHERE habit_id = ? AND user_id = ?
        """,
        (habit_id, session["user_id"])
    )

    connection.execute(
        """
        DELETE FROM habits
        WHERE id = ? AND user_id = ?
        """,
        (habit_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    flash("Habit deleted successfully.")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)