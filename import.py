import csv, os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def create_user_table():
    db.execute("DROP TABLE IF EXISTS Users")
    db.execute("""CREATE TABLE Users(id SERIAL PRIMARY KEY, 
                                     Username TEXT NOT NULL, 
                                     Hash TEXT NOT NULL)""")
    db.commit()

def create_books_table():
    db.execute("DROP TABLE IF EXISTS Books")
    db.execute("""CREATE TABLE Books(id SERIAL PRIMARY KEY, 
                                     Title TEXT NOT NULL, 
                                     Author TEXT, 
                                     Year INT, 
                                     ISBN TEXT NOT NULL)""")
    db.commit()


def import_data():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO Books (Title, Author, Year, ISBN) VALUES (:title, :author, :year, :isbn)",
                     {"title": title, "author": author, "year": year, "isbn": isbn})
    db.commit()

if __name__ == "__main__":
    # create_user_table()
    # create_books_table()
    # import_data()
    pass
