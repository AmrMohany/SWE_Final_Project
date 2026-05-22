from flask import Flask, render_template
from database import init_db

app = Flask(__name__)

app.secret_key = "habit_tracker_secret_key"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init-db")
def initialize_database():
    init_db()
    return "Database initialized successfully!"


if __name__ == "__main__":
    app.run(debug=True)