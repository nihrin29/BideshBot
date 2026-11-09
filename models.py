"""
Database tables for BideshBot (SRS section 7.1).

Each class below is one table. Each "db.Column" is one column in that table.
SQLAlchemy turns these Python classes into real database tables for us.
"""

from datetime import datetime

from flask_login import UserMixin

from extensions import db, login_manager


# ---------------------------------------------------------------
# Users and profiles
# ---------------------------------------------------------------

class User(UserMixin, db.Model):
    """A registered student account."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)       # never the real password (NFR-06)
    accepted_privacy_notice = db.Column(db.Boolean, default=False)  # NFR-30
    failed_logins = db.Column(db.Integer, default=0)                # NFR-10
    locked_until = db.Column(db.DateTime)                           # NFR-10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One user has one profile. Deleting the user deletes everything they own (FR-07).
    profile = db.relationship("Profile", backref="user", uselist=False, cascade="all, delete-orphan")
    saved = db.relationship("SavedScholarship", backref="user", cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="user", cascade="all, delete-orphan")
    chat_sessions = db.relationship("ChatSession", backref="user", cascade="all, delete-orphan")


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login calls this on every page to find the logged-in user by their ID."""
    return db.session.get(User, int(user_id))


class Profile(db.Model):
    """A student's academic profile (FR-08 to FR-15)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Step 1 (FR-08)
    target_degree = db.Column(db.String(20))         # "Bachelor", "Master" or "PhD"
    preferred_countries = db.Column(db.String(100))  # e.g. "USA,UK" or "Any"
    field_of_study = db.Column(db.String(100))
    nationality = db.Column(db.String(50), default="Bangladesh")  # FR-14

    # Bachelor's applicants (FR-09)
    school_qualification = db.Column(db.String(20))  # "SSC/HSC", "O/A-Level" or "Other"
    secondary_result = db.Column(db.Float)           # SSC or O-Level
    secondary_scale = db.Column(db.Float)
    higher_secondary_result = db.Column(db.Float)    # HSC or A-Level
    higher_secondary_scale = db.Column(db.Float)

    # Master's and PhD applicants (FR-10, FR-11)
    bachelor_cgpa = db.Column(db.Float)
    bachelor_scale = db.Column(db.Float)
    institution = db.Column(db.String(150))
    graduation_year = db.Column(db.Integer)
    work_experience_years = db.Column(db.Float)

    # PhD applicants only (FR-11)
    master_cgpa = db.Column(db.Float)
    master_scale = db.Column(db.Float)
    research_area = db.Column(db.String(150))
    publications = db.Column(db.Integer)
    research_experience_years = db.Column(db.Float)

    # Optional yearly budget in US dollars (FR-15)
    yearly_budget_usd = db.Column(db.Float)

    test_scores = db.relationship("TestScore", backref="profile", cascade="all, delete-orphan")


class TestScore(db.Model):
    """One English or admission test result (FR-12)."""
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id"), nullable=False)
    test_type = db.Column(db.String(50))   # "IELTS", "TOEFL iBT", "GRE", "SAT" or another name
    status = db.Column(db.String(30))      # "Not taken", "Awaiting result" or "Score available"
    score = db.Column(db.Float)


# ---------------------------------------------------------------
# Scholarships
# ---------------------------------------------------------------

class Scholarship(db.Model):
    """One scholarship listing (FR-27 to FR-35, FR-52)."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(50), nullable=False)        # USA, UK, Germany or Canada
    degree_levels = db.Column(db.String(50))                  # e.g. "Master,PhD"
    fields = db.Column(db.String(255))                        # eligible fields, or "Any"
    summary = db.Column(db.Text)                              # short summary only (NFR-29)

    # Funding (FR-28, FR-29)
    funding_type = db.Column(db.String(30))       # "Full funding", "Partial funding" or "Tuition waiver"
    tuition_coverage = db.Column(db.String(255))  # e.g. "100%", "50%", "USD 5,000 per year"
    stipend = db.Column(db.String(255))           # living allowance, or "Not stated"
    other_benefits = db.Column(db.String(255))
    not_covered = db.Column(db.String(255))       # what is not covered
    tuition_fee = db.Column(db.Float)             # yearly tuition, if published
    tuition_currency = db.Column(db.String(10))
    is_departmental_funding = db.Column(db.Boolean, default=False)  # FR-35

    required_documents = db.Column(db.Text)       # one document per line (FR-31)
    deadline = db.Column(db.Date)                 # empty = "Deadline not confirmed" (FR-25)

    application_url = db.Column(db.String(500), nullable=False)  # FR-32, NFR-21
    source_url = db.Column(db.String(500), nullable=False)       # FR-34, NFR-21

    status = db.Column(db.String(20), default="Published")  # Published, Rejected, Hidden or Expired
    last_collected = db.Column(db.DateTime)                 # FR-34
    last_changed = db.Column(db.DateTime)                   # FR-34
    manually_corrected = db.Column(db.Boolean, default=False)  # FR-59

    requirements = db.relationship("Requirement", backref="scholarship", cascade="all, delete-orphan")


class Requirement(db.Model):
    """One eligibility rule of a scholarship (SRS 7.1 and 7.2)."""
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"), nullable=False)
    criterion = db.Column(db.String(50))       # e.g. "IELTS", "CGPA", "Degree level", "Nationality"
    is_hard = db.Column(db.Boolean, default=False)  # hard = failing it makes the student ineligible
    value = db.Column(db.String(100))          # the required value, e.g. "6.5" or "Bangladesh"
    grading_scale = db.Column(db.Float)        # e.g. 4.0 for a CGPA requirement
    alternative_group = db.Column(db.String(50))  # same group = any one is enough (IELTS or TOEFL)
    is_unknown = db.Column(db.Boolean, default=False)  # FR-54: not clear on the source page


class SourcePage(db.Model):
    """A web page visited by the collection job (FR-50, FR-55)."""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    seed_source = db.Column(db.String(255))
    page_hash = db.Column(db.String(64))   # fingerprint of the page text (FR-55)
    last_visited = db.Column(db.DateTime)


# ---------------------------------------------------------------
# Student activity
# ---------------------------------------------------------------

class SavedScholarship(db.Model):
    """A scholarship a student has saved (FR-36)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    scholarship = db.relationship("Scholarship")


class Report(db.Model):
    """A student's report that a listing is wrong (FR-38)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"), nullable=False)
    reason = db.Column(db.String(50))   # incorrect requirement, wrong deadline, broken link, other
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatSession(db.Model):
    """One chat conversation (FR-48)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("ChatMessage", backref="session", cascade="all, delete-orphan")


class ChatMessage(db.Model):
    """One message inside a chat conversation (FR-48)."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_session.id"), nullable=False)
    sender = db.Column(db.String(10))      # "student" or "assistant"
    text = db.Column(db.Text)
    sources = db.Column(db.Text)           # links of scholarships cited (FR-43)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CollectionLog(db.Model):
    """A record of one collection run (FR-58)."""
    id = db.Column(db.Integer, primary_key=True)
    run_at = db.Column(db.DateTime, default=datetime.utcnow)
    pages_visited = db.Column(db.Integer, default=0)
    records_added = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_rejected = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text)
