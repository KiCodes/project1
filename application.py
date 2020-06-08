import os, requests, sys, logging

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not 'postgres://aqahhdthxrjyvy:63df43f030494c880de7ec470986b3374e28c5ef9854ac45b35c13261a1a5878@ec2-46-137-84-140.eu-west-1.compute.amazonaws.com:5432/dff93k8u1ucr6r':
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://aqahhdthxrjyvy:63df43f030494c880de7ec470986b3374e28c5ef9854ac45b35c13261a1a5878@ec2-46-137-84-140.eu-west-1.compute.amazonaws.com:5432/dff93k8u1ucr6r')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "V5HqQjNCtfaNGnWnDoSQ", "isbns": "0375913750"})
    print(res.json())

if __name__ == "__main__":
    main()
