import os
import random

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, datetime, get_values

# Time
date_time = datetime.datetime.now()

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    holdings = db.execute("SELECT * FROM holdings WHERE UserID = ? AND Shares > 0 ORDER BY Symbol", session["user_id"])

    # Obtain holdings and cash balance; if holdings found add current price to list
    cash_balance = float(db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"])
    if holdings:
        for holding in holdings:
            holding["Price"] = lookup(holding["Symbol"])["price"]
    return render_template("index.html", holdings=holdings, cash_balance=cash_balance)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Check for valid input for symbol
        symbol_input = request.form.get("symbol")
        if not symbol_input or not lookup(symbol_input):
            return apology("Invalid symbol")
        symbol = lookup(symbol_input)

        # Check for valid input for shares and valid number of shares
        shares_input = request.form.get("shares")
        if not shares_input or not shares_input.isnumeric() or not float(shares_input).is_integer() or int(shares_input) < 1:
            return apology("Invalid symbol or shares has to be greater than 0 and an integer")
        shares = int(shares_input)

        # Compute purchase: obtain price of symbol via price key, convert to float to retain 2 decimal places and * shares
        value = float(symbol["price"]) * shares

        # Obtain user's cash balance
        cash_balance = float(db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"])

        # Check for sufficient funds, insert data into table, update balance for user
        if cash_balance < value:
            return apology("insufficient funds")
        db.execute(
                   """
                   INSERT INTO transactions (Type, UserID, Symbol, Price, Shares, Total, Date)
                   VALUES('Buy', ?, ?, ?, ?, ?, ?)
                   """,
                   session["user_id"], symbol["symbol"], symbol["price"], shares, value, date_time)

        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", value, session["user_id"])

        # If symbol not found in holding insert new row entry, else update shares for symbol
        if len(db.execute("SELECT * FROM holdings WHERE symbol = ?", symbol["symbol"])) == 0:
            db.execute(
                """
                INSERT INTO holdings (UserID, Symbol, Shares)
                VALUES(?, ?, ?)
                """,
                session["user_id"], symbol["symbol"], shares)
        else:
            db.execute("UPDATE holdings SET Shares = Shares + ? WHERE Symbol = ? AND UserID = ?", shares, symbol["symbol"], session["user_id"])

        flash("Bought!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions WHERE UserID = ?", session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Obtains form input for username, checks for username in db, check if conditions
        username = request.form.get("username")
        username_exists = db.execute("SELECT username FROM users WHERE username = ?", username)
        if not username or username_exists:
            return apology("Input is Blank or Username Exists")

        # Obtains form input for password and checks if conditions, then generate hash
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or password != confirmation:
            return apology("Passwords Do Not Match")
        hash = generate_password_hash(password, method='scrypt', salt_length=16)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # Obtains output of lookup, checks for a return value from lookup, pass argument into quoted.html
        symbol = lookup(request.form.get("symbol"))
        if not symbol:
            return apology("Invalid Symbol")

        return render_template("quoted.html", symbol=symbol)
    else:
        return render_template("quote.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Change password"""

    # Load page and generate random math problem to store in session because
    # Code is executed each time a request is sent and so question will be different
    if request.method == "GET":
        first_number = random.randrange(100)
        second_number = random.randrange(100)
        operators = ["+", "-", "*"]
        operation = random.choice(operators)
        expression = f"{first_number} {operation} {second_number}"
        answer = eval(expression)
        session["answer"] = answer
        session["problem"] = expression
        return render_template("account.html", expression=expression)

    if request.method == "POST" and request.form.get("accountPassword") == "1":
        # Check for valid password input, and if hash of current password input matches hash in db
        current_password = request.form.get("password")
        if not current_password:
            return apology("Password input is blank")
        stored_hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]["hash"]
        if not check_password_hash(stored_hash, current_password):
            return apology("Incorrect password")

        # Check for a match for new password and confirmation, hash new password and update db
        new_password = request.form.get("newPassword")
        confirmation = request.form.get("confirmation")
        if new_password != confirmation:
            return apology("Passwords do not match")
        hash_new_password = generate_password_hash(new_password, method='scrypt', salt_length=16)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_new_password, session["user_id"])

        flash("Password changed")
        return redirect("/account")

    if request.method == "POST" and request.form.get("accountBalance") == "1":
        user_answer = request.form.get("answer")
        if int(user_answer) == session["answer"]:
            db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", 10000, session["user_id"])
            flash("Correct! $_$")
            return redirect("/account")
        else:
            db.execute("UPDATE users SET cash = 0 WHERE id = ?", session["user_id"])
            flash("Incorrect! :')")
            return redirect("/account")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    holdings = db.execute("SELECT * FROM holdings WHERE UserID = ? AND Shares > 0 ORDER BY Symbol", session["user_id"])

    # get symbol, shares to be sold, current price
    if request.method == "POST":

        # Check for valid input for symbol and to see if user has shares
        symbol_input = request.form.get("symbol")
        if not symbol_input:
            return apology("Select a stock that you want to sell")
        symbol = lookup(symbol_input)
        if symbol["symbol"] not in get_values("Symbol", holdings):
            return apology("Stock not found")

        # Check for valid input for shares and valid number of shares
        shares_input = request.form.get("shares")
        if not shares_input or not shares_input.isnumeric() or not float(shares_input).is_integer() or int(shares_input) < 1:
            return apology("Invalid input for shares")
        shares = int(shares_input)
        user_shares = db.execute("SELECT Shares FROM holdings WHERE UserID = ? AND Symbol = ?", session["user_id"], symbol["symbol"])[0]["Shares"]
        if shares > user_shares:
            return apology("Invalid number of shares")

        # Update holdings, transactions, and users(cash) tables according to sell
        value = float(symbol["price"]) * shares
        db.execute("UPDATE holdings SET Shares = Shares - ? WHERE UserID = ? AND Symbol = ?", shares, session["user_id"], symbol["symbol"])
        db.execute(
                   """
                   INSERT INTO transactions (Type, UserID, Symbol, Price, Shares, Total, Date)
                   VALUES('Sell', ?, ?, ?, ?, ?, ?)
                   """,
                   session["user_id"], symbol["symbol"], symbol["price"], -abs(shares), value, date_time)
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", value, session["user_id"])

        flash("Sold!")
        return redirect("/")

    return render_template("sell.html", holdings=holdings)

