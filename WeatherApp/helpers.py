import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup_geo(city_name, state_code, country_code):

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        if state_code == None:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={urllib.parse.quote_plus(city_name)},{urllib.parse.quote_plus(country_code)}&limit=1&appid={api_key}"
        else:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={urllib.parse.quote_plus(city_name)},{urllib.parse.quote_plus(state_code)},{urllib.parse.quote_plus(country_code)}&limit=1&appid={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        geo = response.json()

        #json response is a list of dicts so we want the first object
        geo = geo[0]

        return {
            "lat": geo["lat"],
            "lon": geo["lon"],
            "country": geo["country"]
        }

    #added index error exception for when api call brings back empty list
    except (KeyError, TypeError, ValueError, IndexError):
        return None

def lookup_weather(lat, lon, city_name, city_id):
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")

        #request imperial unit weather data
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        weather = response.json()

        return {
            "temp_current": int(weather["main"]["temp"]),
            "temp_min": int(weather["main"]["temp_min"]),
            "temp_max": int(weather["main"]["temp_max"]),
            "city": city_name,
            "city_id": city_id,
            "conditions": weather["weather"][0]["description"]
        }


    except (KeyError, TypeError, ValueError):
        return None
