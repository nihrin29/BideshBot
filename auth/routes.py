"""
Pages for user accounts: register, login and logout (FR-02, FR-03).
"""

from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User

from .forms import LoginForm, RegisterForm

# A blueprint is a group of related pages. All account pages live in this one.
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # A logged-in student doesn't need to register again.
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()

    # validate_on_submit() is True only when the form was sent and every check passed.
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # FR-02: each email can only be used once.
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in.", "error")
            return redirect(url_for("auth.login"))

        # NFR-06: store only a salted hash of the password, never the password itself.
        user = User(
            email=email,
            password_hash=generate_password_hash(form.password.data, method="pbkdf2:sha256"),
            accepted_privacy_notice=True,
        )
        db.session.add(user)
        db.session.commit()

        flash("Your account has been created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            # FR-03: the session ends after 60 minutes of inactivity
            # (the time limit is set in config.py).
            session.permanent = True
            flash("You are now logged in.", "success")
            return redirect(url_for("home"))

        # The same message for a wrong email or a wrong password,
        # so nobody can find out which emails are registered.
        flash("Incorrect email or password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
