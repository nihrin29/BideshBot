"""
Forms for user accounts.

Flask-WTF forms check the input on the server (NFR-07) and
add a hidden CSRF token to every form automatically.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp

# A simple check that the email looks like "name@example.com" (FR-02).
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[
        DataRequired(message="Please enter your email."),
        Regexp(EMAIL_PATTERN, message="Please enter a valid email address."),
        Length(max=255),
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Please enter a password."),
        Length(min=8, message="Password must be at least 8 characters."),  # FR-02
    ])
    confirm_password = PasswordField("Confirm password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords do not match."),
    ])
    accept_privacy = BooleanField("I have read and accept the privacy notice", validators=[
        DataRequired(message="You must accept the privacy notice to register."),  # NFR-30
    ])
    submit = SubmitField("Register")


class DeleteAccountForm(FlaskForm):
    # The student types their password again to confirm (FR-07).
    password = PasswordField("Enter your password to confirm", validators=[
        DataRequired(message="Please enter your password."),
    ])
    submit = SubmitField("Delete my account")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(message="Please enter your email.")])
    password = PasswordField("Password", validators=[DataRequired(message="Please enter your password.")])
    submit = SubmitField("Log in")
