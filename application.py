import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, telephone

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["telephone"] = telephone

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///Brewly.db")
db = SQL(os.getenv("DATABASE_URL"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        requiredFieldnames = ["email", "username", "password", "confirmation"]

        # Ensure username and password was submitted
        for entry in requiredFieldnames:
            if not request.form.get(entry):
                return apology("Fill out all fields", 400)

        # Ensure password and confirmation password match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords must match", 400)

        # Ensure user not alrady registered
        rows = db.execute("SELECT * FROM users WHERE email = :email",
                          email=request.form.get("email"))
        if len(rows) == 1:
            return apology("Email already in use", 400)

        # Ensure user not alrady registered
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) == 1:
            return apology("Username already exists", 400)

        # Add new user to the database
        hash = generate_password_hash(request.form.get("password"))

        new_id = db.execute(
            "INSERT INTO users(username, email, hash) VALUES(:username, :email, :hash)",
            username=request.form.get("username"),
            email=request.form.get("email"),
            hash=hash)

        session["user_id"] = new_id

        return redirect("/")
        

@app.route("/check", methods=["GET"])
def check():
    """Return true if username and email available, else false, in JSON format"""

    print(request.args.get("username"))
    print(request.args.get("email"))

    if request.args.get("username"):
        check = db.execute(
            "SELECT * from users where username = :username",
            username=request.args.get("username"))
        return jsonify(True) if not check else jsonify(False)
    else:
        check = db.execute(
            "SELECT * from users where email = :email",
            email=request.args.get("email"))
        return jsonify(True) if not check else jsonify(False)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/")
# @login_required
def index():
    """Show home page"""
    
    # return render_template("index.html")
    return redirect("/about")


@app.route("/search", methods=["GET", "POST"])
def search():
    """Allow users to search"""

    if request.method == "GET":
        
        # Use db to build list of states with no duplicates
        getStates = db.execute("SELECT DISTINCT state FROM breweries")
        states = []
        for e in getStates:
            if e["state"]:
                states.append(e["state"])
                
        return render_template("search.html",
                states=states)

    
@app.route("/get_cities", methods=["GET", "POST"])
def get_cities():
    """AJAX call. Return cities given a State"""

    if request.method == "GET":
        
        # State selected by user
        state = request.args.get("state")

        # Get brewery info from db based on State
        stateBreweries = db.execute(
            "SELECT * from breweries WHERE state = :state",
            state=state)
         
        # Sort alphabetically on City name    
        stateBreweries = sorted(stateBreweries, key=lambda k: (k["city"]))    
        
        # Use db to build list of Cities
        cities = []
        for brewery in stateBreweries:
            if brewery["city"] not in cities:
                cities.append(brewery["city"])

        return render_template("cities.html",
                      cities=sorted(cities),
                      state=state)


@app.route("/get_breweries", methods=["GET", "POST"])
def get_breweies():
    """AJAX call. Return breweries given a City"""

    if request.method == "GET":
        
        # City & State as selected by user
        city = request.args.get("city")
        state = request.args.get("state")
        
        if city:
            # Get brewery info from db based on City & State
            cityBreweries = db.execute(
                    "SELECT * from breweries WHERE city = :city AND state = :state",
                    city=city,
                    state=state)
            breweries = cityBreweries        
        else:
            # Get brewery info from db based on State
            stateBreweries = db.execute(
                    "SELECT * from breweries WHERE state = :state",
                    state=state)
            city = ""        
            breweries = sorted(stateBreweries, key=lambda k: (k["city"]))        
            

        # Generate link to map based on brewery address
        # Removing map link based on latitude and longitude since data is unreliable
        for brewery in breweries:
            if brewery["street"]:
                brewery["map"] = "https://maps.google.com/?q="+brewery["street"].replace(" ","+")+"+"+brewery["city"].replace(" ","+")+"+"+brewery["state"].replace(" ","+")
            # elif brewery["longitude"]:
            #     brewery["map"] = "http://maps.google.com/?ll="+str(brewery["latitude"])+","+str(brewery["longitude"])
            else:
                brewery["map"] = brewery["street"]
  
            # Need to know if there is a loged on user in order to correctly 
            # indicate favorite breweries in the search results display
            if session.get('user_id') != None:
                user=session['user_id']
            else:
                user = 0
            
            # Add a "favorite" dictionary key to indicate if user has favorited brewery    
            userFavs = db.execute(
            "SELECT * from favorites WHERE userID = :user AND breweryID = :breweryID",
            user=user,
            breweryID = brewery["id"])    
            if len(userFavs) == 1:
                brewery["favorite"] = True
            
        return render_template("search_results.html",
                      breweries=breweries,
                      city=city,
                      state=state)


@app.route("/about", methods=["GET", "POST"])
def about():
    """Display About page"""

    if request.method == "GET":
        return render_template("about.html")

@app.route("/add_brewery", methods=["GET", "POST"])
def add_brewery():
    """Allow users to submit new breweries"""

    if request.method == "GET":

        # Get list of States. No duplicates
        getStates = db.execute("SELECT DISTINCT state FROM breweries")
        states = []
        for e in getStates:
            if e["state"]:
                states.append(e["state"])
        
        return render_template("add_brewery.html",
        states=states)
        
    if request.method == "POST":
        # Variableize user input
        state = request.form.get("state")
        city = request.form.get("city")
        name = request.form.get("name")
        street = request.form.get("street")
        zip = request.form.get("zip")
        phone = request.form.get("phone")
        website = request.form.get("website")
        
        # Store user input into storage table
        new_brewery = db.execute(
                    "INSERT INTO newBrewery(name, state, city, street, zip, phone, website)"
                    "VALUES(:name, :state, :city, :street, :zip, :phone, :website)",
                    name=name,
                    state=state,
                    city=city,
                    street=street,
                    zip=zip,
                    phone=phone,
                    website=website)
                    
        return redirect("/add_brewery")
        

@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
    """Allow users to save their favorite breweries"""

    if request.method == "GET":
        
        # Use db to gather user favortes
        userFavs = db.execute(
            "SELECT * from breweries JOIN favorites ON breweries.id = favorites.breweryID WHERE favorites.userID = :user",
            user=session['user_id'])

        # Generate link to map based on brewery address
        # Removing map link based on latitude and longitude since data is unreliable
        for brewery in userFavs:
                if brewery["street"]:
                    brewery["map"] = "https://maps.google.com/?q="+brewery["street"].replace(" ","+")+"+"+brewery["city"].replace(" ","+")+"+"+brewery["state"].replace(" ","+")
                # elif brewery["longitude"]:
                #     brewery["map"] = "http://maps.google.com/?ll="+str(brewery["latitude"])+","+str(brewery["longitude"])
                else:
                    brewery["map"] = brewery["street"]
                    
        # Display favorites in alphabetical order on State name            
        userFavs = sorted(userFavs, key=lambda k: (k["state"], k["city"]))              

        return render_template("favorites.html",
                    breweries=userFavs)


@app.route("/update_favorites", methods=["GET", "POST"])
@login_required
def update_favorites():
    """AJAX call. Update user favorites from checkboxes"""

    # Update favorites db table based upon checkbox clicks
    if request.method == "GET":
        checkbox = request.args.get("checkbox")
        id = request.args.get("id")
        print(checkbox)
        print(id)
        
        if checkbox == "true":
            # Ensure favorite not alrady in database
            favCheck = db.execute("SELECT * FROM favorites WHERE userID = :userID AND breweryID = :breweryID",
                          userID=session['user_id'],
                          breweryID=id)
            
            # Add new favorite if not already stored for that user              
            if len(favCheck) == 0:              
                newFav = db.execute(
                        "INSERT INTO favorites(userID, breweryID) VALUES(:userID, :breweryID)",
                        userID=session['user_id'],
                        breweryID=id)
        else:
            # Favorite checkbox was unchecked. Remove favorite
            unFav = db.execute(
                  "DELETE from favorites WHERE userID = :userID AND breweryID = :breweryID",
                  userID=session["user_id"], breweryID=id)
        
        return redirect("/favorites")

    
def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
