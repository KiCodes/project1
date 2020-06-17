import os, requests
import json

from flask import Flask, render_template, session, jsonify, request, url_for, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_debug import Debug
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized
from passlib.hash import sha256_crypt


app = Flask(__name__)

# Check for environment variable
if not 'postgres://fxyzakjbntiyba:7ec5988e2651ec94203b7641eb38f0f88a654ef472887849ceac2ed259a22ebf@ec2-46-137-124-19.eu-west-1.compute.amazonaws.com:5432/d1ru6railneec7':
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://fxyzakjbntiyba:7ec5988e2651ec94203b7641eb38f0f88a654ef472887849ceac2ed259a22ebf@ec2-46-137-124-19.eu-west-1.compute.amazonaws.com:5432/d1ru6railneec7')
db = scoped_session(sessionmaker(bind=engine))

class DuplicateValueException(Exception):   
    def __init__(self, data):    
        self.data = data
    def __str__(self):
        return repr(self.data)


@app.route("/")
def index():
    if session.get("log"):
        return render_template("index_user.html")
    
    return render_template("index.html")

@app.route("/login")
def loginpage():
    """Log in page"""
    if session.get("log"):
        return redirect(url_for('search'))
    
    return render_template("login.html")

@app.route("/signup")
def signup():
    """sign up page"""
    return render_template("signup.html")

@app.route("/adduser", methods=["POST"])
def adduser():
    """add user"""   
    # Get form information.
    name = request.form.get("fullname")
    user = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm = request.form.get("confirm")
    secure_password=sha256_crypt.encrypt(str(password))
        
    usernamedata=db.execute("SELECT username FROM users WHERE username=:username",{"username":user}).fetchone()
    emaildata=db.execute("SELECT email FROM users WHERE email=:email",{"email":email}).fetchone()
		#usernamedata=str(usernamedata)
    if usernamedata==None:
        if password==confirm:
            db.execute("INSERT INTO users (fullname, username, email, password) VALUES (:fullname, :username, :email, :password)", {"fullname": name, "username": user, "email": email, "password":secure_password})
            db.commit()
        else:
            return render_template('signup.html', message="password does not match")   
    else:
        return render_template('signup.html', message="user already exists")
        
    return render_template("login.html", message="you have successfully signed up")
    


    
@app.route("/signin", methods=["POST"])
def signin():
    """sign in"""
    username=request.form.get("username")
    password=request.form.get("password")
    
    usernamedata=db.execute("SELECT username FROM users WHERE username=:username",{"username":username}).fetchone()
    passworddata=db.execute("SELECT password FROM users WHERE username=:username",{"username":username}).fetchone()
    
    if usernamedata==None:
        return render_template('login.html', message="No username exists")
    else:
        for passwor_data in passworddata:
            if sha256_crypt.verify(password,passwor_data):
                session["log"]=usernamedata
                print(session["log"])
            else:
                return render_template('login.html', message="incorrect password")
    return render_template('search.html', message="you are now logged in")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")

@app.route("/search")
def search():
    """search page"""
    if session.get("log") is None:
        return render_template("search_anon.html", message="you need to log in first")
    
    books = db.execute("SELECT * FROM books").fetchall()
    
    return render_template("search.html", books=books)

@app.route("/booklist", methods=["POST"])
def booklist():
    """search for review"""
    if session.get("log") is None:
        return render_template("error.html", message="you need to log in first")
    
    searchfor=request.form.get("searchfor")
    
    searchfor = "%{}%".format(searchfor)
        
    bookisbn = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn ORDER BY title ASC", {"isbn":searchfor}).fetchall()
        
    booktitle = db.execute("SELECT * FROM books WHERE title LIKE :title ORDER BY title ASC", {"title": "%" + searchfor + "%"}).fetchall()
        
    bookauthor = db.execute("SELECT * FROM books WHERE author LIKE :author ORDER BY title ASC", {"author":searchfor}).fetchall()
    
    if searchfor == None or searchfor == "":
        return render_template("search.html", message="cannot be empty"), 400
    
    else:
        
        if bookisbn or booktitle or bookauthor:
            flash("you got it", "success")
    
        else:
            return render_template("search.html", message="no books"), 404
        
    return render_template("booklist.html", bookisbn=bookisbn, booktitle=booktitle, bookauthor=bookauthor)




@app.route("/bookdetails/<int:this_book_id>")
def bookdetails(this_book_id):
    """list book details and review"""
    
    if session.get("log") is None:
        return render_template("error.html", message="you need to log in first")
    
    my_book = db.execute("SELECT * FROM books WHERE id = :this_id", {"this_id": this_book_id}).fetchone()
    
    #extract goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "V5HqQjNCtfaNGnWnDoSQ", "isbns": my_book.isbn})
    x = res.json()
    y = json.dumps(x)
    z = json.loads(y)
    v = z["books"]
    info = v[0]
    average_rating = info["average_rating"]
    work_ratings_count = info["work_ratings_count"]
    
    #select other user reviews
    reviews = db.execute("SELECT * FROM reviews WHERE books_id = :this_id", {"this_id": this_book_id}).fetchall()
        
    return render_template("review.html", id=this_book_id, book=my_book, reviews=reviews, rating=average_rating, rcount=work_ratings_count)
        
@app.route("/reviewsubmit/<int:this_book_id>",methods=["GET", "POST"])
def reviewsubmit(this_book_id):
    """submit review"""
    if session.get("log") is None:
        return render_template("error.html", message="you need to log in first")
    
    this_user=session["log"][0]
    b_id=this_book_id
    print(this_user)
    rtng=request.form.get("rating")
    cmnt=request.form.get("comment")
  #Check if the same user already have an review in database  
    getreview=db.execute("SELECT * FROM reviews WHERE user_name = :this_usr AND books_id = :this_bk",{"this_usr": this_user, "this_bk": b_id}).fetchone()
    print(getreview)
    
    if rtng is None or cmnt is None:
        return render_template("error_rev.html", message="rating or comment cannot be empty")
    
    if getreview is None:#if not let him review the book
        db.execute("INSERT INTO reviews (books_id, user_name, rating, review) VALUES (:books_id, :user_name, :rating, :review)", {"books_id":b_id,"user_name": this_user, "rating": rtng, "review": cmnt})
        db.commit()
        flash("successfully reviewed","success")
    else:
        return render_template("error_rev.html", message="cannot submit more than once")
    
    return render_template("submit_review.html")

@app.route("/api/<string:isbn>")
def api(isbn):
    my_book = db.execute("SELECT * FROM books WHERE isbn=:this_isbn",{"this_isbn":isbn}).fetchone()
    if my_book is None:#if ISBN notexist in Databse throw  404 error page
        return render_template("404.html"),404
    res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "V5HqQjNCtfaNGnWnDoSQ", "isbns":isbn})
    x=res.json()
    y=json.dumps(x)
    z=json.loads(y)
    v=z["books"]
    info=v[0]
    av_rating=info["average_rating"]
    rv_count=info["reviews_count"]
    return render_template("api.html",book=my_book,av_score=av_rating,rv_count=rv_count)


if __name__=='__main__':app.run()