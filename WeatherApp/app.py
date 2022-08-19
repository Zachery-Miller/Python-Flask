import os
import csv
import logging
import pandas as pd

from re import match
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from helpers import apology, login_required, lookup_geo, lookup_weather

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///weather.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Configure upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Configure max file upload size
max_MB = 16
app.config['MAX_CONTENT_LENGTH'] = max_MB * (1024 * 1024)

# configure allowable file extensions
app.config['ALLOWED_EXTENSIONS'] = ['.csv']

# configure log directory and file
app.config['LOG_FOLDER'] = 'logfolder'
app.config['LOG_FILE'] = 'log.txt'

# configure template directory and file and columns
app.config['TEMPLATE_FOLDER'] = 'uploadtemplate'
app.config['TEMPLATE_FILE'] = 'uploadtemplate.csv'
app.config['TEMPLATE_COLUMNS'] = ['city_name', 'state_code', 'country_code', 'lat', 'lon', 'country (2 letter)']


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    #get user_id
    userid = session["user_id"]

    #fetch user dash data
    dash_data = db.execute("SELECT * FROM dashboard JOIN cities ON dashboard.city_id = cities.city_id WHERE user_id = ?", userid)

    #create list to store lists/dicts
    city_list = []

    #make api call and add output to city_list for each city in user dashboard
    for row in dash_data:
        weather_data = lookup_weather(row["lat"], row["lon"], row["city_name"], row["city_id"])
        city_list.append(weather_data)

    return render_template("index.html", city_list=city_list)


@app.route("/login", methods=["GET", "POST"])
def login():

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        #flash login message
        flash("You were successfully logged in!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was submitted
        elif not request.form.get("confirmation"):
            return apology("must repeat password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) == 0:
            #insert new username and pw hash into db
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)", request.form.get("username"), generate_password_hash(request.form.get("password")))


        elif len(rows) != 0:
            return apology("the username " + request.form.get("username") + " already exists", 403)

        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    #if page is reached via POST
    if request.method == "POST":

        #get user session
        userid = session["user_id"]
        rows = db.execute("SELECT * FROM users WHERE id = ?", userid)

        #check old password is entered
        if not request.form.get("oldpw"):
            return apology("Must enter old password to continue", 403)

        #check new password is entered
        if not request.form.get("newpw"):
            return apology("Must enter a new password to continue", 403)

        #check new password is entered twice
        if not request.form.get("confirmation"):
            return apology("Must enter new password again to confirm", 403)

        #check current password is entered correctly
        if not check_password_hash(rows[0]["hash"], request.form.get("oldpw")):
            return apology("Current password is incorrect!", 403)

        #check new password is entered correctly twice
        if request.form.get("newpw") != request.form.get("confirmation"):
            return apology("New passwords do not match!", 403)

        #check new password is not the same as current password
        if check_password_hash(rows[0]["hash"], request.form.get("newpw")):
            return apology("This password is the same as your old one, please submit a new password", 403)

        #if all checks are passed, update user password
        rows = db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("newpw")), userid)

        #flash login message
        flash("Password changed successfully!")

        #return to dashboard
        return redirect("/")

    #render page if reached via GET
    return render_template("account.html")


@app.route("/addcitydash", methods=["GET", "POST"])
@login_required
def addcitydash():

    if request.method == "POST":
        #prepare data for db entry
        userid = session["user_id"]
        cityid = request.form.get("city")

        #check if the selected city is already on users dashboard
        rows = db.execute("SELECT * FROM dashboard where user_id = ? AND city_id = ?", userid, cityid)

        #if city is not on dashboard, add it
        if len(rows) == 0:
            db.execute("INSERT INTO dashboard (user_id, city_id) VALUES (?,?)", userid, cityid)
            cityname = db.execute("SELECT * FROM cities where city_id = ?", cityid)
            cityname = cityname[0]["city_name"].title()
            flash(f"{cityname} added to dashboard!")

        #if city is on dashboard, show apology
        if len(rows) != 0:
            return apology("this city is already on your dashboard!", 403)

        #get db data for dropdown
        citylist = db.execute("SELECT * FROM cities order by city_name")

        return redirect("/")

    #get db info for dropdown
    citylist = db.execute("SELECT * FROM cities order by city_name")

    return render_template("addcitydash.html", citylist=citylist)

@app.route("/addcitydb", methods=["GET", "POST"])
@login_required
def addcitydb():

    if request.method == "POST":

        #create variables for city name and country code base on form input
        cityname = request.form.get("cityname").title()
        countrycode = request.form.get("countrycode")


        # Ensure a city name was submitted
        if not cityname:
            return apology("must provide a city name", 403)

        # Ensure country code was submitted
        elif not countrycode:
            return apology("must provide country code", 403)

        #set state code to None if nothing is entered, otherwise assign to input
        if not request.form.get("statecode"):
            statecode = None
        else:
            statecode = request.form.get("statecode")

        #make API to to geocoder API
        geo_data = lookup_geo(cityname, statecode, countrycode)

        if geo_data != None:
            rows = db.execute("SELECT * FROM cities WHERE city_name = ? AND country_code = ?", cityname, countrycode)
        else:
            return apology("api call failed, please try correcting city name and country code", 403)

        if len(rows) == 0:
            db.execute("INSERT INTO cities (city_name, state_code, country_code, lat, lon, country) VALUES (?, ?, ?, ?, ?, ?)", cityname, statecode, countrycode, geo_data["lat"], geo_data["lon"], geo_data["country"])
            flash(f'{cityname} has been added to the database!')

        if len(rows) != 0:
            return apology("city already exists in database", 403)

        return render_template("addcitydb.html")

    else:
        return render_template("addcitydb.html")

@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    #reached via POST
    if request.method == "POST":
        #get user session
        userid = session["user_id"]
        cityid = request.form.get("removecity")

        #delete city from dashboard
        db.execute("DELETE FROM dashboard WHERE user_id = ? AND city_id = ?", userid, cityid)
        cityname = db.execute("SELECT * FROM cities WHERE city_id = ?", cityid)
        cityname = cityname[0]["city_name"].title()

        #flash removed message
        flash(f"{cityname} removed from dashboard!")

        #refresh dashboard
        return redirect("/")

    #reached via GET (no href this shouldnt happen)
    return redirect("/")

@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():

    #reached via POST
    if request.method == "POST":
        #get user session
        userid = session["user_id"]

        #get answer from form
        answer = request.form.get("answer")

        #if answer is yes, clear session and delete user data from DB
        if answer == "yes":
            session.clear()
            db.execute("DELETE FROM dashboard WHERE user_id = ?", userid)
            db.execute("DELETE FROM users WHERE id = ?", userid)

        #return to login
        return redirect("/login")

    #reached via GET, shouldnt happen as there is no href
    return redirect("/")

@app.route("/fileupload", methods=["POST"])
@login_required
def upload():

    try:
        # get file from html and get extension type
        file = request.files['file']
        extension = os.path.splitext(file.filename)[1]

        # if there is a file, check extension is allowed (make sure it is a .csv)
        if file:
            if extension not in app.config['ALLOWED_EXTENSIONS']:
                return apology("File extension not allowed! Please upload .csv files only!")

        # save file for later reference
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))

        # if there is no file selected when upload is clicked, flash message letting user know to select a csv file for upload
        if not file:
            flash("No file selected! Please select a .csv file for upload.")
            return redirect('/addcitydb')

    # if file size is too large, render apology
    except RequestEntityTooLarge:
        return apology("File size is larger than the max 16MB!")

    # call the process function to read csv into database
    success, warn, fail = process()

    #flash messages
    #no data
    if success == 0 and warn == 0 and fail == 0:
        flash("Upload failed. No data in file. Please resubmit file containing data.")

    #not using template
    elif success == -1 and warn == -1 and fail == -1:
        flash("Please use only the template file for uploads. Please do not alter the column titles.")

    #default output
    else:
        flash(f"File uploaded with {success} successful row(s), {fail} failed row(s), and {warn} warning(s). Please review log file for more detailed information.")

    #delete upload file from directory after processing
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))

    return redirect('/addcitydb')

def process():
    #get file from uploads folder
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file = os.path.join(app.config['UPLOAD_FOLDER'], files[0])

    #open and read file to a list of dicts
    with open(file, "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    #validate template file and return negative values for success, warn, fail if not template
    try:
        df = pd.read_csv(file)
        list_of_column_names = list(df.columns)
        print(list_of_column_names)

    except:
        return -1, -1, -1

    if list_of_column_names != app.config['TEMPLATE_COLUMNS']:
        return -1, -1, -1


    #set counters for successful insert, warning, failure for message flash
    total_row_errors = 0
    total_row_success = 0
    total_row_warn = 0

    #set line variable to excel row where data starts for error logging through upload file
    line = 1

    #set lat/lon increment range
    lat_lon_range = 0.5

    # configure handler and start logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(filename="logfolder/log.txt", level=logging.DEBUG,
                        format="%(asctime)s %(levelname)-8s %(message)s", filemode="w")

    #start log
    logging.debug(f"Attempting DB upload for {file}")


    for row in data:
        line += 1
        row_errors = 0
        #log current line in excel file
        logging.info(f"Processing line {line} of upload file")

        #implement logic checks
        if match("^[a-zA-z]+\s?[a-zA-Z]+\s?[a-zA-Z]+\s?$", row["city_name"]) == None:
            row_errors += 1
            logging.error("City name is not alphabetic or was not entered. Please update city name to only alphabetic characters.")

        if row["state_code"]:
            state_code = row["state_code"]
            if not state_code.isnumeric():
                row_errors += 1
                logging.error("State code is not numeric. Please update state code to only numeric characters")

        if row["state_code"] == "":
            state_code = None

        if not row["country_code"].isnumeric():
            row_errors += 1
            logging.error("Country code is not numeric or was not entered. Please update country code to only numeric characters")

        if match("^-?(0|[1-9]\d*)(\.\d+)?$", row["lat"]) == None:
            row_errors += 1
            logging.error(f"Lat \'{row['lat']}\' is not numeric or was not entered. Please update lat to only numeric characters with the exception of '-' and '.'")

        if match("^-?(0|[1-9]\d*)(\.\d+)?$", row["lon"]) == None:
            row_errors += 1
            logging.error(f"Lon \'{row['lon']}\' is not numeric or was not entered. Please update lon to only numeric characters with the exception of '-' and '.'")

        if not row["country (2 letter)"].isalpha():
            row_errors += 1
            logging.error("Country is not alphabetic or was not entered. Please update country to only alphabetic characters")

        if len(row["country (2 letter)"]) != 2:
            row_errors += 1
            logging.error("Country is not 2 letters in length or was not entered. Please update country to its 2 letter abbreviation")



        #log errors if any
        if row_errors == 0:
            warn = 0
            #check if city or town exists in db
            #checks lat/lon input in case a town or city has the same name in the country ----- ?+0.5 0.5 is meant to represent a roughly 30 mile difference
            check_row = db.execute("SELECT * FROM cities WHERE city_name = ? AND country_code = ? AND country = ? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
                                    row["city_name"].title(), row["country_code"], row["country (2 letter)"].upper(),
                                    float(row["lat"])-lat_lon_range, float(row["lat"])+lat_lon_range, float(row["lon"])-lat_lon_range, float(row["lon"])+lat_lon_range)

            #if already exists in db log warning and don't submit to db
            if len(check_row) != 0:
                cityname = row["city_name"].title()
                country = row["country (2 letter)"].upper()
                logging.warning(f"{cityname}, {country} already exists in the database! This line will not submit to database.")
                warn += 1
                total_row_warn += 1

            #if does not exist in db, submit and log
            if len(check_row) == 0:
                cityname = row["city_name"].title()
                country = row["country (2 letter)"].upper()

                db.execute("INSERT INTO cities (city_name, state_code, country_code, lat, lon, country) VALUES (?, ?, ?, ?, ?, ?)",
                            cityname, state_code, row["country_code"], row["lat"], row["lon"], row["country (2 letter)"].upper())
                logging.info(f"{cityname}, {country} entered into DB successfully")

                total_row_success += 1

            #logging for no errors or warnings. logging for warnings
            if warn == 0:
                logging.info(f"No errors or warnings found in line {line}")
            else:
                logging.info(f"{warn} warning found in line {line}")

        #logging for errors
        if row_errors != 0:
            logging.warning(f"{row_errors} error(s) found in line {line}")

        #update total row errors for flash message after upload,
        if row_errors > 0:
            total_row_errors += 1

    #stop logging and return error counters
    if total_row_success == 0 and total_row_warn == 0 and total_row_errors == 0:
        logging.error("No data in upload file")

    logging.shutdown()
    return total_row_success, total_row_warn, total_row_errors




# download log file from upload
@app.route('/downloadlogs', methods=["GET", "POST"])
@login_required
def download_logs():

    #if post
    if request.method == "POST":
        return redirect(url_for('log_file', filename=app.config['LOG_FILE']))

    #if get
    return render_template("logs.html")

# log attachment download route
@app.route('/logfolder/<filename>')
def log_file(filename):
    return send_from_directory(app.config['LOG_FOLDER'], filename, as_attachment = True)




# download upload template for db upload
@app.route('/downloadtemplate', methods=["GET", "POST"])
@login_required
def download_template():

    #if post
    if request.method == "POST":
        return redirect(url_for('template_file', filename=app.config['TEMPLATE_FILE']))

    #if get
    return render_template("addcitydb.html")

# upload template attachment download route
@app.route('/uploadtemplate/<filename>')
def template_file(filename):
    return send_from_directory(app.config['TEMPLATE_FOLDER'], filename, as_attachment = True)