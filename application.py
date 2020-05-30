import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    username = request.form.get("username")
    if request.method == "POST":
        print(f"POST {username}", flush=True)
    elif request.method == "GET":
        print(f"GET {username}", flush=True)
    else:
        print(f"meh {username}", flush=True)

    return render_template("signup.html")


goodreads_api_key = "SdD1S2KiCOWfPmTLyhbrA"
goodreads_api_secret = "9EdAKZcsPeJfbrvx9spqGmKkfpciXnshhJyk0s18Q"
