import csv, os
from sqlalchemy import create_engine

engine = create_engine(os.getenv("DATABASE_URL"))
conn = engine.connect()


def create_books_table():
    conn.execute("CREATE TABLE IF NOT EXISTS Books(Title TEXT, Author TEXT, Year INT, ISBN INT)")


def import_data():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        conn.execute("INSERT INTO Books (Title, Author, Year, ISBN) VALUES (:title, :author, :year, :isbn)",
                     {"title": title, "author": author, "year": year, "isbn": isbn})
    print(f"Added {title}")


if __name__ == "__main__":
    create_books_table()
    import_data()
