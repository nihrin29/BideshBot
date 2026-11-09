"""
Shared tools used by the whole website.

They are created here, in one place, so every module can import them
without importing app.py (which would cause a circular import).
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# The database connection (SQLAlchemy is our ORM, NFR-07).
db = SQLAlchemy()

# Keeps track of which user is logged in (FR-03).
login_manager = LoginManager()

# Protects every form against cross-site request forgery (NFR-07).
csrf = CSRFProtect()
