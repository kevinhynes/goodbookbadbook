import os
from flask import Flask, session, request, render_template, url_for, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/books")
def books():
    books = db.execute("SELECT * from Books").fetchall()
    return render_template("books.html", books=books)


@app.route("/authors")
def authors():
    books = db.execute("SELECT * from Books").fetchall()
    return render_template("authors.html", books=books)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    username = request.form.get("username")
    pwd = request.form.get("pwd")
    repeat_pwd = request.form.get("repeat_pwd")
    if request.method == "POST":
        print(f"POST {username}", flush=True)
        if validate_registration(username, pwd, repeat_pwd):
            hash = generate_password_hash(pwd)
            print(f"registration validated {username, pwd, hash}", flush=True)
            db.execute("INSERT INTO Users(Username, Hash) VALUES (:username, :hash)",
                       {"username": username, "hash": hash})
            db.commit()
            flash("Registration successful.", category="success")
            return redirect(url_for('login'))
    return render_template("signup.html")


def validate_registration(username, pwd, repeat_pwd):
    existing_user = db.execute("SELECT * from Users WHERE Username = :username",
                               {"username": username}).fetchone()
    print(f"validate_registration {existing_user}")
    if existing_user:
        print(f"Username unavailable.", flush=True)
        flash("Username unavailable.", category="error")
        return False
    if pwd != repeat_pwd:
        print(f"Passwords do not match.", flush=True)
        flash("Passwords do not match.", category="error")
        return False
    return True


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/test")
def test():
    flash("TESTINGGG")
    return render_template("test.html")


goodreads_api_key = "SdD1S2KiCOWfPmTLyhbrA"
goodreads_api_secret = "9EdAKZcsPeJfbrvx9spqGmKkfpciXnshhJyk0s18Q"
