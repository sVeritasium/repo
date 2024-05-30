import re

from flask import redirect, render_template, request, session
from functools import wraps


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