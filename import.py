import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres://aqahhdthxrjyvy:63df43f030494c880de7ec470986b3374e28c5ef9854ac45b35c13261a1a5878@ec2-46-137-84-140.eu-west-1.compute.amazonaws.com:5432/dff93k8u1ucr6r')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year":year})
        print(f"added {title} by {author} {year} to library")
    db.commit()

if __name__ == "__main__":
    main()
