"""
The starting point of the BideshBot website.

Run it with:  python app.py
Then open http://127.0.0.1:5000 in a browser.
"""

from flask import Flask, render_template

from config import Config
from extensions import csrf, db, login_manager


def create_app():
    """Build the Flask website and connect all its parts."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect the shared tools to this website.
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import the models so SQLAlchemy knows about every table.
    import models  # noqa: F401

    # FR-04: guests who open a page that needs login are sent to the login page.
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in or register to use this feature."

    # Connect each group of pages (blueprint).
    from auth import auth_bp
    from student_profile import profile_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)

    # Create any database tables that don't exist yet.
    with app.app_context():
        db.create_all()

    # Home page.
    @app.route("/")
    def home():
        return render_template("index.html")

    return app


app = create_app()

if __name__ == "__main__":
    # debug=True shows errors in the browser and reloads when code changes.
    # Only for development on my computer, never on the live website.
    app.run(debug=True)
