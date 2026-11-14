"""
Settings for the BideshBot website.

Secret values (like SECRET_KEY) are NOT written here.
They are read from the .env file, which is never uploaded to GitHub (NFR-08).
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

# Read the values from the .env file into the environment.
load_dotenv()


class Config:
    # Used by Flask to sign session cookies and protect forms (CSRF).
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Where the database is. SQLite file on my computer, PostgreSQL online.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///bideshbot.db")

    # Turn off a Flask-SQLAlchemy feature we don't use (saves memory).
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # FR-03: a session ends after 60 minutes of inactivity.
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

    # NFR-07: session cookies cannot be read by JavaScript.
    SESSION_COOKIE_HTTPONLY = True

    # FR-30: approximate exchange rates used to turn tuition fees into US dollars.
    # How many US dollars one unit of each currency is worth. Update these by hand now and then.
    EXCHANGE_RATES_TO_USD = {"USD": 1.0, "GBP": 1.30, "EUR": 1.15, "CAD": 0.72}
