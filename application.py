import os
from flask import Flask, session, request, render_template, url_for, redirect, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import functools
import requests

app = Flask(__name__)


# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

goodreads_api_key = "SdD1S2KiCOWfPmTLyhbrA"
goodreads_api_secret = "9EdAKZcsPeJfbrvx9spqGmKkfpciXnshhJyk0s18Q"

DATABASE_URL = "postgres://ptmrfpvcfmsizq:7f83f5d65df0a7c6cfc6af9727298623597efdada2c02b0d5cd035c5eda787d3@ec2-3-216-129-140.compute-1.amazonaws.com:5432/d2ssl9jq5udmv7"
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
        # print(f"wrapper flashes: {session.get('_flashes', [])}, args: {args}, kwargs: {kwargs}", flush=True)
        if "logged_in" in session:
            return route_func(*args, **kwargs)
        else:
            flash("You must log in to use GoodBookBadBook.", category="error")
            return redirect(url_for('login'))
    return wrapper


@app.route("/signup", methods=["GET", "POST"])
def signup():
    username = request.form.get("username")
    pwd = request.form.get("pwd")
    repeat_pwd = request.form.get("repeat_pwd")
    # print(f"signup flashes: {session.get('_flashes', [])}", flush=True)
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
    existing_user = db.execute("SELECT * FROM Users WHERE Username = :username",
                               {"username": username}).fetchone()
    # print(f"validate_registration flashes: {session.get('_flashes', [])}", flush=True)
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
    # print(f"login flashes: {session.get('_flashes', [])}", flush=True)
    if request.method == "POST":
        existing_user = db.execute("SELECT * FROM Users WHERE Username = :username",
                                   {"username": username}).fetchone()
        if not existing_user:
            flash("No user found. Please sign up first.", category="error")
            return redirect(url_for('signup'))
        if not check_password_hash(existing_user.hash, pwd):
            flash("Incorrect password.", category="error")
            return
        else:
            session["logged_in"] = True
            session["username"] = username
            # flash("Login successful. Thank you for using GoodBookBadBook.", category="success")
            return redirect(url_for('main'))
    return render_template("login.html")


@app.route("/logout")
def logout():
    # print(f"logout flashes: {session.get('_flashes', [])}", flush=True)
    session.pop("logged_in", None)
    session.pop("username", None)
    flash("You have successfully been logged out. Come back soon!", category="success")
    return render_template("logout.html", logged_in=session.get("logged_in", False))


@app.route("/")
def index():
    # print(f"index flashes: {session.get('_flashes', [])}", flush=True)
    return render_template("index.html", logged_in=session.get("logged_in", False))


@app.route("/main")
@login_required
def main():
    # print(f"main flashes: {session.get('_flashes', [])}", flush=True)
    return render_template("main.html", logged_in=session.get("logged_in", False))


@app.route("/books")
@login_required  # calls wrapper() with arguments to books().
def books():
    # print(f"books flashes: {session.get('_flashes', [])}", flush=True)
    books = db.execute("SELECT * FROM Books ORDER BY Title ASC").fetchall()
    return render_template("books.html", books=books, logged_in=session.get("logged_in", False))


@app.route("/books/<int:book_id>", methods=["GET", "POST"])
@login_required  # calls wrapper() with arguments to books().
def book(book_id):
    # print(f"book flashes: {session.get('_flashes', [])}", flush=True)
    if request.method == "POST":
        user_review = request.form.get("user_review")
        user_rating = request.form.get("rating")
        username = session["username"]
        existing_review = db.execute("""SELECT * FROM Reviews WHERE BookID = :book_id
                                        AND Username = :username""",
                                     {"book_id": book_id, "username": username}).fetchone()
        if existing_review:
            flash("You've already submitted a review for this book.", category="error")
        else:
            db.execute("""INSERT INTO Reviews(BookID, Username, UserReview, UserRating)
                          VALUES(:book_id, :username, :user_review, :user_rating)""",
                          {"book_id": book_id, "username": username, "user_review": user_review,
                           "user_rating": user_rating})
            db.commit()

        print(f"book() user_review: {user_review,user_rating}", flush=True)
    reviews = db.execute("""SELECT * FROM Reviews WHERE BookID = :book_id""",
                         {"book_id": book_id}).fetchall()

    book = db.execute("SELECT * FROM Books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": goodreads_api_key, "isbns": book.isbn})
    book_data = res.json()["books"][0]
    rating = book_data["average_rating"]
    rating_width = str((float(rating) / 5) * 100) + "%"
    ratings_count = book_data["ratings_count"]
    return render_template("book.html", book=book, rating=rating, rating_width=rating_width,
                           ratings_count=ratings_count, reviews=reviews,
                           logged_in=session.get("logged_in", False))


@app.route("/authors")
@login_required  # calls wrapper() with arguments to authors().
def authors():
    # print(f"authors flashes: {session.get('_flashes', [])}", flush=True)
    books = db.execute("SELECT DISTINCT Author FROM Books ORDER BY Author ASC").fetchall()
    return render_template("authors.html", books=books, logged_in=session.get("logged_in", False))


@app.route("/authors/<string:author_name>")
@login_required  # calls wrapper() with arguments to books().
def author(author_name):
    # print(f"author flashes: {session.get('_flashes', [])}", flush=True)
    results = db.execute("SELECT * FROM Books WHERE Author IN (:author) ORDER BY Title ASC",
                       {"author": author_name}).fetchall()
    return render_template("author.html", results=results, logged_in=session.get("logged_in", False))


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    # print(f"authors flashes: {session.get('_flashes', [])}", flush=True)
    results = []
    query = '%' + request.form.get("search_query") + '%'
    results += db.execute("SELECT * FROM Books WHERE Title LIKE (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * FROM Books WHERE Author LIKE (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * FROM Books WHERE Year LIKE (:query)", {"query": query}).fetchall()
    results += db.execute("SELECT * FROM Books WHERE ISBN LIKE (:query)", {"query": query}).fetchall()
    return render_template("search.html", results=results, logged_in=session.get("logged_in", False))


@app.route("/api/<string:isbn>")
def book_api(isbn):
    book = db.execute("SELECT * FROM Books WHERE ISBN = :isbn", {"isbn": isbn}).fetchone()
    if not book:
        return jsonify({"error": "Invalid ISBN"}), 422
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": goodreads_api_key, "isbns": book.isbn})
    book_data = res.json()["books"][0]
    return jsonify({"title": book.title,
                    "author": book.author,
                    "year": book.year,
                    "isbn": book.isbn,
                    "review_count": book_data["work_reviews_count"],
                    "average_score": book_data["average_rating"]})
