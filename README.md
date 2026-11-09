# BideshBot

Intelligent Scholarship Discovery and Study-Abroad Assistance System.

BideshBot helps Bangladeshi students find scholarships for Bachelor's, Master's and PhD
study in the USA, UK, Germany and Canada. It checks a student's profile against each
scholarship's requirements, explains the result, and links every listing to its official source.

Course project for CSE 3200 – Design Project II, University of Liberal Arts Bangladesh (Fall 2026).

## Technologies

- **Python + Flask**: web server
- **HTML, CSS, JavaScript**: web pages
- **SQLAlchemy**: database access (SQLite for local development, PostgreSQL online)
- **Flask-Login, Flask-WTF**: login sessions and form protection

## Project structure

```
app.py               Starts the website
config.py            Settings (secrets are read from .env)
extensions.py        Shared tools: database, login manager, CSRF protection
models.py            Database tables
auth/                User accounts
student_profile/     Academic profile
matching/            Rule-based matching engine
collection/          Automated data collection
chat/                AI chat assistant
templates/           HTML pages
static/css/          Styles
```

## How to run it on your computer

1. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install the packages:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your own `SECRET_KEY`.
4. Start the website:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

The database tables are created automatically the first time the website starts.
