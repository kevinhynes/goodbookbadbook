import os
from flask import Flask, session, request, render_template, url_for, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import functools

app = Flask(__name__)


# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

DATABASE_URL = "postgres://xqmbmqkcvpavvs:17f6f6f690bb777e4d484e3ee441e3b4d8c88591d239a9beb49aca4599863b97@ec2-52-70-15-120.compute-1.amazonaws.com:5432/dfg72kp1ckutig"
app.config["DATABASE_URL"] = DATABASE_URL

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
# engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))


def login_required(route_func):
    @functools.wraps(route_func)  # returns wrapper as route_func (?).
    def wrapper(*args, **kwargs):
        print(f"wrapper flashes: {session.get('_flashes', [])}", flush=True)
        if "logged_in" in session:
            return route_func(*args, **kwargs)
        else:
            flash("You must log in to use GoodBookBadBook.", category="error")
            return redirect(url_for('login'))
    return wrapper


@app.route("/")
def index():
    print(f"index flashes: {session.get('_flashes', [])}", flush=True)
    return render_template("index.html", logged_in=session.get("logged_in", False))


@app.route("/main")
@login_required
def main():
    print(f"main flashes: {session.get('_flashes', [])}", flush=True)
    return render_template("main.html", logged_in=session.get("logged_in", False))


@app.route("/books")
@login_required  # calls wrapper() with arguments to books().
def books():
    print(f"books flashes: {session.get('_flashes', [])}", flush=True)
    books = db.execute("SELECT * from Books ORDER BY Title ASC").fetchall()
    return render_template("books.html", books=books, logged_in=session.get("logged_in", False))


@app.route("/books/<int:book_id>")
@login_required  # calls wrapper() with arguments to books().
def book(book_id):
    print(f"book flashes: {session.get('_flashes', [])}", flush=True)
    book = db.execute("SELECT * from Books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    print(f"book() /books/book_id {book}", flush=True)
    return render_template("book.html", book=book, logged_in=session.get("logged_in", False))


@app.route("/authors")
@login_required  # calls wrapper() with arguments to authors().
def authors():
    print(f"authors flashes: {session.get('_flashes', [])}", flush=True)
    books = db.execute("SELECT DISTINCT Author from Books ORDER BY Author ASC").fetchall()
    return render_template("authors.html", books=books, logged_in=session.get("logged_in", False))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    username = request.form.get("username")
    pwd = request.form.get("pwd")
    repeat_pwd = request.form.get("repeat_pwd")
    print(f"signup flashes: {session.get('_flashes', [])}", flush=True)
    if request.method == "POST":
        if validate_registration(username, pwd, repeat_pwd):
            hash = generate_password_hash(pwd)
            db.execute("INSERT INTO Users(Username, Hash) VALUES (:username, :hash)",
                       {"username": username, "hash": hash})
            db.commit()
            flash("Registration successful.", category="success")
            return redirect(url_for('login'))
    return render_template("signup.html")


def validate_registration(username, pwd, repeat_pwd):
    existing_user = db.execute("SELECT * from Users WHERE Username = :username",
                               {"username": username}).fetchone()
    print(f"validate_registration flashes: {session.get('_flashes', [])}", flush=True)
    if existing_user:
        flash("Username unavailable.", category="error")
        return False
    if len(username) < 3:
        flash("Username must be at least 3 characters", category="error")
        return False
    if pwd != repeat_pwd:
        flash("Passwords do not match.", category="error")
        return False
    if len(pwd) < 3:
        flash("Password must be at least 3 characters.", category="error")
        return False
    return True


@app.route("/login", methods=["GET", "POST"])
def login():
    username = request.form.get("username")
    pwd = request.form.get("pwd")
    print(f"login flashes: {session.get('_flashes', [])}", flush=True)
    if request.method == "POST":
        existing_user = db.execute("SELECT * from Users WHERE Username = :username",
                                   {"username": username}).fetchone()
        if not existing_user:
            flash("No user found. Please sign up first.", category="error")
            return redirect(url_for('signup'))
        if not check_password_hash(existing_user.hash, pwd):
            flash("Incorrect password.", category="error")
            return
        else:
            session["logged_in"] = True
            flash("Login successful. Thank you for using GoodBookBadBook.", category="success")
            return redirect(url_for('main'))
    return render_template("login.html")


@app.route("/logout")
def logout():
    # session.pop("_flashes", None)
    print(f"logout flashes: {session.get('_flashes', [])}", flush=True)
    session.pop("logged_in", None)
    flash("You have successfully been logged out. Come back soon!", category="success")
    return render_template("logout.html", logged_in=session.get("logged_in", False))


@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    query = request.form.get("search_query")
    results += db.execute("SELECT * from Books WHERE Title IN (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * from Books WHERE Author IN (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * from Books WHERE Year IN (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * from Books WHERE ISBN IN (:query)", {"query": query}).fetchall()
    return render_template("search.html", results=results, logged_in=session.get("logged_in", False))


goodreads_api_key = "SdD1S2KiCOWfPmTLyhbrA"
goodreads_api_secret = "9EdAKZcsPeJfbrvx9spqGmKkfpciXnshhJyk0s18Q"
