import random
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, get_flashed_messages, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Time
date_time = datetime.datetime.now()

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

@app.after_request
def after_request(response):
    """Ensure responds aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Checks for valid username input
        username = request.form.get("username")
        username_exists = db.execute("SELECT 1 FROM users WHERE username = ?", username)
        if not username or username_exists:
            flash("Invalid username or username exists")
            return render_template("register.html")
        
        # Checks for valid password input
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or password != confirmation:
            flash("Invalid password")
            return render_template("register.html")
        hash = generate_password_hash(password, method='scrypt', salt_length=16)
        db.execute("INSERT INTO users (username, hash, date) VALUES (?, ?, ?)", username, hash, date_time)

        session.clear()
        flash("Please login")
        return render_template("login.html")
    else:
        return render_template("register.html")

@app.route("/entry", methods=["POST"])
@login_required
def entry():
    line = request.form.get("line")
    # Need to add conditions for criteria
    db.execute("INSERT INTO lines (line, user_id, date) VALUES (?, ?, ?)", line, session["user_id"], date_time)

    return render_template("index.html")

@app.route("/get_entries", methods=["GET"])
def get_entries():
    """Fetch three random lines from the database"""
    lines = db.execute("SELECT line FROM lines ORDER BY RANDOM() LIMIT 3")

    formatted_lines = []
    if random.randrange(2) == 1:
        for i, line in enumerate(lines):
            if i > 0:
                parts = line["line"].split(';')
                formatted_lines.append({
                    "line": parts[0]
                })
            else:
                formatted_lines.append(line)
    else:
        for i, line in enumerate(lines):
            if i < 2:
                parts = line["line"].split(';')
                formatted_lines.append({
                    "line": parts[0]
                })
            else:
                formatted_lines.append(line)
    
    return jsonify(formatted_lines)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Clear user session
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Invalid username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid username and/or password")
            return render_template("login.html")

        # Clear session and remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")