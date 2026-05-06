from flask import Flask, render_template

app = Flask(__name__)

app.secret_key = "habit_tracker_secret_key"


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)