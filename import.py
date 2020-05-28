import csv, os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def create_books_table():
    db.execute("DROP TABLE IF EXISTS Books")
    db.execute("CREATE TABLE IF NOT EXISTS Books(Title TEXT, Author TEXT, Year INT, ISBN TEXT)")
    db.commit()


def import_data():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO Books (Title, Author, Year, ISBN) VALUES (:title, :author, :year, :isbn)",
                     {"title": title, "author": author, "year": year, "isbn": isbn})
    db.commit()

if __name__ == "__main__":
    create_books_table()
    import_data()
