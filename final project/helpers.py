import re
import random

from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def validate_entry(entry):
    # Checks to see if entry follows 1 of 2 patterns
    pattern1 = re.compile(r"^With (\w+), comes (\w+); (\w+(\s\w+){0,3})$", re.IGNORECASE)
    pattern2 = re.compile(r"Without (\w+), no (\w+); (\w+(\s\w+){0,3})$", re.IGNORECASE)

    if pattern1.match(entry) or pattern2.match(entry):
        return True
    else:
        return False
    
def transform_line(line):
    # Transform line to capitalize first word and lowercase the rest
    if line.lower().startswith("with "):
        return "With " + line[5:].lower()
    elif line.lower().startswith("without "):
        return "Without " + line[8:].lower()
    else:
        return line
    
def random_format(lines):
    # Transform lines according to randomly assigned format
    formatted_lines = []
    if random.randrange(2) == 1:
        formatted_lines.append({
            "poem_type": "s"
        })
        for i, line in enumerate(lines):
            if i > 0:
                parts = line["line"].split(';')
                formatted_lines.append({
                    "id": line["id"],
                    "line": parts[0]
                    
                })
            else:
                formatted_lines.append(line)
    else:
        formatted_lines.append({
            "poem_type": "e"
        })
        for i, line in enumerate(lines):
            if i < 2:
                parts = line["line"].split(';')
                formatted_lines.append({
                    "id": line["id"],
                    "line": parts[0]
                })
            else:
                formatted_lines.append(line)
    return formatted_lines

def check_liked(user_id, poem_type, line1_id, line2_id, line3_id):
    liked = db.execute("""
                       SELECT 1 FROM likes WHERE user_id = ? AND poem_type = ? AND line1_id = ? AND line2_id = ? AND line3_id = ?
                       """, 
                       user_id, poem_type, line1_id, line2_id, line3_id
                       )
    if liked:
        return True
    else:
        return False