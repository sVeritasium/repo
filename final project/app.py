import datetime
import random

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, get_flashed_messages, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, validate_entry, transform_line, random_format, check_liked

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

@app.context_processor
def inject_user():
    return dict(username=session.get("username"))

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
        session["username"] = rows[0]["username"]


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


@app.route("/entry", methods=["POST"])
@login_required
def entry():
    """Handles user's submission of line"""
    line = request.form.get("line")

    # Checks if line fits formats
    if not validate_entry(line):
        flash("Invalid entry format")
        return render_template("index.html", line=line)
    
    # Checks if line already exists
    elif db.execute("SELECT 1 FROM lines WHERE line LIKE ?", f"%{transform_line(line)}%"):
        flash("Sorry, line already exists")
        return render_template("index.html", line=line)
    
    db.execute("INSERT INTO lines (line, user_id, date) VALUES (?, ?, ?)", transform_line(line), session["user_id"], date_time)
    return render_template("index.html")


@app.route("/customize", methods=["POST"])
@login_required
def customize():
    """Returns user's data to display lines in modal"""
    user_data = db.execute("SELECT id, line, date FROM lines WHERE user_id = ? ORDER BY date", session["user_id"])
    return jsonify(user_data)


@app.route("/get_entries", methods=["GET"])
def get_entries():
    """Fetch three random lines from the database"""
    customize = request.args.get("customize", type=int)
    poem_id = request.args.get("poemID", type=int)
    formatted_lines = []

    # Checks for selected line
    if customize == 1:
        custom_lines = db.execute("""SELECT * FROM (
                   SELECT id, line FROM lines WHERE id = ?
                   UNION ALL
                   SELECT * FROM (SELECT id, line FROM lines ORDER BY RANDOM() LIMIT 2))
                   ORDER BY RANDOM();
                   """, poem_id
                   )
        formatted_lines = random_format(custom_lines)
    else:    
        lines = db.execute("SELECT id, line FROM lines ORDER BY RANDOM() LIMIT 3")
        formatted_lines = random_format(lines)

    response_data = {"lines": formatted_lines}
    return jsonify(response_data)

        # --- test ---
        # if random.randrange(2) == 1:
        #     formatted_lines = [
        #         {'poem_type': 's'}, {'id': 64, 'line': 'With rainbows, comes magic; skies light up'}, {'id': 91, 'line': 'Without questions, no answers'}, {'id': 49, 'line': 'Without time, no healing'}
        #     ]
        # else:
        #     formatted_lines = [
        #         {'poem_type': 'e'}, {'id': 64, 'line': 'With bananas, comes magic; skies light up'}, {'id': 91, 'line': 'Without doom, no answers'}, {'id': 49, 'line': 'Without space, no healing'}
        #     ]


@app.route("/like", methods=["GET", "POST"])
@login_required
def like():
    if request.method == "POST":
        """Handle like button click"""
        lines = request.json.get("lines")
        poem_type = request.json.get("poem_type")

        # Check for inputs
        if not lines or len(lines) != 3 or not poem_type:
            return jsonify({"error": "Please try again"}), 400

        # Check if the like already exists
        liked = check_liked(session["user_id"], poem_type, lines[0]["id"], lines[1]["id"], lines[2]["id"])
        if liked:
            # If liked, delete the like
            db.execute("""
                       DELETE FROM likes WHERE user_id = ? AND poem_type = ? AND line1_id = ? AND line2_id = ? AND line3_id = ?
                       """, session.get("user_id"), poem_type, lines[0]["id"], lines[1]["id"], lines[2]["id"]
                       )
            success = True
            liked_status = False
        else:
            # If not liked, insert a new like
            db.execute("""
                       INSERT INTO likes (user_id, poem_type, line1_id, line1, line2_id, line2, line3_id, line3, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """,
                       session["user_id"], poem_type, lines[0]["id"], lines[0]["text"], lines[1]["id"], lines[1]["text"], lines[2]["id"], lines[2]["text"], date_time
                       )
            success = True
            liked_status = True

        return jsonify({"success": success, "liked": liked_status})
    else:
        """Fetch like status and count for the current set of lines"""
        lines = request.args.getlist("lines[]")
        poem_type = request.args.get("poem_type")

        # Check for inputs
        if not lines or len(lines) != 3 or not poem_type:
            return jsonify({"error": "Please try again"}), 400

        # Check if user has liked the poem
        liked = None
        if "user_id" in session:
            liked = check_liked(session["user_id"], poem_type, lines[0], lines[1], lines[2])

        # Count likes for poem
        likes_count = db.execute("""
                           SELECT COUNT(*) AS count FROM likes WHERE poem_type = ? AND line1_id = ? AND line2_id = ? AND line3_id = ?
                           """,
                           poem_type, lines[0], lines[1], lines[2]
                           )[0]["count"]

        return jsonify({"liked": liked, "likes": likes_count})

@app.route("/notepad", methods=["GET", "POST"])
def notepad():
    """Display user's lines and allows for deletion"""
    user_data = db.execute("SELECT id, line, date FROM lines WHERE user_id = ? ORDER BY date", session["user_id"])

    # Delete line
    if request.method == "POST":
        line_id = request.form.get("delete_line")
        if not line_id:
            flash("Error encountered when deleting")
            return render_template("notepad.html", user_data=user_data)
        try:
            db.execute("DELETE FROM lines WHERE user_id = ? AND id = ?", session["user_id"], line_id)
            flash("Line successfully deleted")
            return redirect("/notepad")
        except:
            flash("Error: Line cannot be deleted due to it having been weaved into a poem and appreciated")
            return redirect("/notepad")
        
    return render_template("notepad.html", user_data=user_data)

@app.route("/syncs", methods=["GET", "POST"])
def syncs():
    liked_poems = db.execute("SELECT * FROM likes WHERE user_id = ?", session["user_id"])

    # Count likes for poem
    # likes = db.execute("""
    #                    SELECT COUNT(*) AS count FROM likes WHERE poem_type = ? AND line1_id = ? AND line2_id = ? AND line3_id = ?
    #                    """,
    #                    formatted_lines[0]["poem_type"], formatted_lines[1]["id"], formatted_lines[2]["id"], formatted_lines[3]["id"]
    #                    )
    
    
    
    return render_template("syncs.html", liked_poems=liked_poems)