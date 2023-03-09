import sqlite3
import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = sqlite3.connect("data.db", check_same_thread = False)
cur = db.cursor()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
          error = "Please enter a username"
          return render_template("login.html", error = error)

         #Ensure password was submitted
        elif not request.form.get("password"):
            error = "Please enter a password"
            return render_template("login.html", error = error)

        # Query database for username
        rows = cur.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
        result = rows.fetchall()

        # Ensure username exists and password is correct
        if len(result) != 1 or not check_password_hash(result[0][2], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("login.html", error = error)

        # Remember which user has logged in
        session["user_id"] = result[0][0]

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
    # User reached route via GET
    if request.method == "GET":
        return render_template("register.html")

    else:
        # get info from the form
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        # check if username is empty
        if not username:
            error = "Please enter a username"
            return render_template("register.html", error = error)

        # check if password is empty
        if not password:
            error = "Please enter a password"
            return render_template("register.html", error = error)

        # check if confirm password is empty
        if not confirm:
            error = "Please confirm your password"
            return render_template("register.html", error = error)

        # check if password and confirm password match
        if password != confirm:
            error = "Passwords not match"
            return render_template("register.html", error = error)

        hash = generate_password_hash(password)

        # Insert into the table
        try:
             new = cur.execute("INSERT INTO users (username, password) VALUES(?, ?)", (username, hash))
             db.commit()
        except:

            error = "User already exists"
            return render_template("register.html", error = error)

        session["user_id"] = new.fetchall()

        return redirect("/")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # get user id
    user = session["user_id"]

    #get info
    my_event = cur.execute("SELECT event FROM event WHERE user_id =?", str(user))
    show_event = my_event.fetchall()

    #return the data to the template
    return render_template("index.html", events = show_event)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        events = request.form.get("event")
        user = session["user_id"]

        # check if symbol is empte
        if not events:
            error = "Please enter a event"
            return render_template("index.html", error = error)

        date = datetime.date.today()

        cur.execute("INSERT INTO event (user_id, event, date) VALUES(?, ?, ?)", (user, events, date))
        db.commit()

        return redirect("/")

@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        task = request.form.get("task")
        cur.execute("DELETE FROM event WHERE event = ?", [task])
        db.commit()

        return redirect("/")




