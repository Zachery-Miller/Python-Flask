# MyWeather App
#### Video Demo: <https://youtu.be/lLxC-OcQnVk>
#### Description:

Stack: Python, Flask, SQLite3, HTML, CSS, Javascript

The idea behind this project is to create a web-based weather application that utilizes the mentioned stack and OpenWeatherMap's API to fetch weather data for certain cities. I want to be able to create a dashboard application for any user that logs into the app that displays weather information for their pinned cities. An admin account will also be created to control new city entries into the database.

To start with, I created a number of extra directories which will be utilized later. These are: logfolder, uploads, and uploadtemplate. 'logfolder' is use to house the log file which is overwritten with each file upload to submit city data into the database. 'uploads' houses the upload file submitted by the user which should be in csv format (don't worry, the code checks for this :) ). This file should contain data intended to be uploaded into the database. 'uploadtemplate' houses the database upload template to be served to the admin for database uploads. Having a template has helped keep the program from erroring out when the csv data is not formatted as the code intends to read it.

Next there is the default flask directories: static, flask_session (I used filesystem sessions for this implementation), and templates. In the 'static' directory I have a 'weather.ico' file which is being used as the application's favicon on the browser tab. Additionally, I also have my 'styles.css' custom CSS file which I used to improve the interface of my application. I had to tweak several properties in this file in addition to the bootstrap properties I was already taking advantage of to get the look I wanted. As mentioned above the 'flask_session' directory exists to enable filesystem sessions for the application. In the 'templates' directory I have all of the html pages my application renders.

'account.html' - this page contains the form for editing a signed in user's account. You can submit a password change to the form, or you can submit an account deletion to the form. I used Javascript here to control the visibility of the button that actually deletes the user's account. The user first has to select 'delete account' and then confirm with the newly popped up 'yes' button to successfully delete their account. Deleting an account clears all of the user's information from the database tables.

'addcitydash.html' - this page contains the form for adding a city from the database to a user's dashboard so their dashboard can make the necessary API call and get weather data for the city. The dropdown only includes cities that exist in the database.

'addcitydb.html' - this page is an admin-only page. It contains two forms which are used to add new cities into the database. The top form uses OpenWeatherMap's GeoLocator API to find the latitude and longitude of a city and enter it into the database in addition to the user inputs for city name, state code, and country code. I found in testing this was super unreliable. It works ONLY for VERY large cities and even then, sometimes the API call fails. That is where my next idea came in to create a file upload feature where a file containing all the relevant city data to make a weather API call can be submitted all at once. This allows for processing multiple additions to the database, and with a log file output as feedback. I will talk more about the implementation of this later.

'apology.html' - all credits go to the Harvard team that put the course together for this one. I loved the use of this in pset9's Finance problem and so I used it again here for errors that I didn't want to redirect.

'index.html' - this page is the dashboard page. It's the first page the user sees once they log in and the one they are most frequently redirected to. If a user has added cities to their dashboard they will appear here as cards containing weather data for their cities which are removable from the dashboard via a red 'X' button on the cards. If they have no cities this window is blank until a city is added.

'layout.html' - this page is the backbone of my html pages. I used jinja to extend this template to all of my pages to minimize redundant html code and make sitewide changes where applicable. I also include the links to my CSS and bootstrap here.

'login.html' - this page is used to log the user in. The application pages are only accessible once a user is logged in. Not much else to say here

'logs.html' - this page is used by the admin only. Once a file is uploaded to attempt to add new cities to the database, a new log file is created. Clicking the button on this page downloads the latest log file if the admin needs more information as to why a file upload may have had failed, or warning rows.

'register.html' - this page is used to register a new user account. Submitting this form successfully creates a new user in the database who can use the application.

Outside of the directories there are the app.py, helpers.py, requirements.txt and weather.db files.

'app.py' - this is the meat of the project. It controls all of the applications functionality (except what is written in helpers.py) and is used to communicate with both the front-end and the database.

'helpers.py' = this file contains "helper" functions. It contains the apology function which was provided by the Harvard team in pset9, and the login_required decorator which was also provided by the Harvard team in pset9. Additionally it also contains both the geolocator API call function and the weather API call function. These were tucked away here to minimize clutter in the 'app.py' file.

'requirements.txt' - this file is good practice and includes the modules required for this application to function.

'weather.db' - this is the sqlite3 database used for the project. I created only 3 tables in the database as I thought that's all that would be necessary for this implementation. There is a users table - contains usernames and password hashes as well as unique ids for users, a cities table - contains relevant information about a city that is used in the Weather API call, and a dashboard table which is essentially a join table - it contains both user ids and city ids so when a user reaches their dashboard it only displays cities with a city id that matches the user id in this table.


Regarding design choices...

I chose to make this application have an admin and a user. If I were to publish this as a legitimate application I wouldn't want user's having the same DB entry access as an admin. For that reason, certain features are omitted from the user account such as DB entry and log file access. A user can only create an account, update their password, delete their account, add cities to their dashboard, and remove cities from their dashboard. The admin has all of this access as well as the ability to enter new cities into the database and check the log file generated from file uploads to the database.

For front-end design, I wanted something pretty minimal. I didn't feel like a weather application should be overly complicated visually. I wanted to see current weather, highs and lows, and conditions for a handful of cities. I opted for a sidebar navigation because I personally like sidebars for applications with a "dashboard" or "work area" container (I was thinking of ServiceNow as an example of this).

For back-end design, my big design choices were with my database and my filesystem. How much could I reuse? What needed to be new? Are questions I often had.

For the database - I wanted again a very simple table that does what I need it to do. I went through a couple of iterations on paper and landed with my current design - a table containing cities and all the data needed to make the Weather API call, a user table containing usernames and passwords, and a table to join the two tables. I don't believe any other tables are necessary for this implementation. Several columns in the database were mandatory and so they were assigned to be NOT NULL. The app.py file also goes through several data cleaning and processing steps, as well as assesses logic for NULL situations before entering anything into the database. This design in my opinion felt lightweight and still robust. As far as what I could reuse from files - I did my best to keep certain pages of a similar style (this is good not just for back-end but front-end experience as well). For example, login, register, and account pages are all very similar in looks visually - on the backend they aren't much different either besides the functions they call in app.py and the commands they pass to the database. This made implementing these functions pretty simple. The other pages were a bit more unique and required more attention and tweaking on both the frontend and the backend.