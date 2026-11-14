"""
Pages for browsing scholarships (FR-01, FR-25, FR-27 to FR-35).

/scholarships              list with keyword search and filters (guests can use it)
/scholarships/<id>         details page with the 7 sections
"""

import re
from datetime import date

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user
from sqlalchemy import or_

from models import Scholarship

scholarships_bp = Blueprint("scholarships", __name__, url_prefix="/scholarships")

# Choices shown in the filter boxes. The first value is saved in the database, the second is shown.
COUNTRIES = [("USA", "United States"), ("UK", "United Kingdom"), ("Germany", "Germany"), ("Canada", "Canada")]
DEGREES = [("Bachelor", "Bachelor's"), ("Master", "Master's"), ("PhD", "PhD")]
FUNDING_TYPES = ["Full funding", "Partial funding", "Tuition waiver"]

# Short country codes for the small badge on each card, e.g. "UK".
COUNTRY_CODES = {"USA": "US", "UK": "UK", "Germany": "DE", "Canada": "CA"}


def visible_scholarships():
    """
    Only scholarships students may see: published, and deadline not passed.
    A scholarship with no deadline stays visible but is labelled "Deadline not confirmed" (FR-25).
    """
    return Scholarship.query.filter(
        Scholarship.status == "Published",
        or_(Scholarship.deadline.is_(None), Scholarship.deadline >= date.today()),
    )


def days_left(deadline):
    """Number of days until the deadline, or None if there is no deadline (FR-33)."""
    if deadline is None:
        return None
    return (deadline - date.today()).days


def covered_percent(scholarship):
    """
    How much of the tuition is covered, as a number from 0 to 100, or None if we can't tell.
    Reads values like "100%", "50% of tuition" or "Full tuition" from tuition_coverage.
    """
    text = (scholarship.tuition_coverage or "").lower()
    match = re.search(r"(\d+(\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1))
    if text.startswith("full"):
        return 100.0
    return None


def remaining_tuition_usd(scholarship):
    """
    FR-30: the approximate yearly tuition the student still has to pay, in US dollars.
    Only worked out when both the tuition fee and the coverage are recorded.
    """
    percent = covered_percent(scholarship)
    if scholarship.tuition_fee is None or percent is None:
        return None
    rates = current_app.config["EXCHANGE_RATES_TO_USD"]
    rate = rates.get(scholarship.tuition_currency)
    if rate is None:              # unknown currency: better to show nothing than a wrong number
        return None
    remaining = scholarship.tuition_fee * (100 - percent) / 100
    return remaining * rate


def budget_warning(scholarship):
    """True when the remaining tuition is higher than the logged-in student's budget (FR-30)."""
    if not current_user.is_authenticated or current_user.profile is None:
        return False
    budget = current_user.profile.yearly_budget_usd
    remaining = remaining_tuition_usd(scholarship)
    if budget is None or remaining is None:
        return False
    return remaining > budget


@scholarships_bp.route("/")
def list_page():
    # Read the search box and filters from the address bar, e.g. /scholarships?country=UK
    keyword = request.args.get("q", "").strip()
    country = request.args.get("country", "")
    degree = request.args.get("degree", "")
    funding = request.args.get("funding", "")

    query = visible_scholarships()

    # Keyword search in the title, provider, fields and summary (FR-01).
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(Scholarship.title.ilike(like), Scholarship.provider.ilike(like),
                                 Scholarship.fields.ilike(like), Scholarship.summary.ilike(like)))
    if country:
        query = query.filter(Scholarship.country == country)
    if degree:
        # degree_levels is saved like "Master,PhD", so we look for the word inside it.
        query = query.filter(Scholarship.degree_levels.contains(degree))
    if funding:
        query = query.filter(Scholarship.funding_type == funding)

    # Soonest deadline first; scholarships without a deadline go last.
    scholarships = query.order_by(Scholarship.deadline.is_(None), Scholarship.deadline,
                                  Scholarship.title).all()

    return render_template("scholarships/list.html", scholarships=scholarships,
                           keyword=keyword, country=country, degree=degree, funding=funding,
                           countries=COUNTRIES, degrees=DEGREES, funding_types=FUNDING_TYPES,
                           country_codes=COUNTRY_CODES, days_left=days_left,
                           budget_warning=budget_warning)


@scholarships_bp.route("/<int:scholarship_id>")
def details(scholarship_id):
    # Hidden, rejected or expired scholarships can't be opened.
    scholarship = visible_scholarships().filter(Scholarship.id == scholarship_id).first()
    if scholarship is None:
        abort(404)

    # Required documents are saved one per line (FR-31).
    documents = [line.strip() for line in (scholarship.required_documents or "").splitlines()
                 if line.strip()]

    # "Master,PhD" -> "Master's, PhD"
    degree_names = dict(DEGREES)
    degree_text = ", ".join(degree_names.get(d.strip(), d.strip())
                            for d in (scholarship.degree_levels or "").split(",") if d.strip())

    return render_template("scholarships/details.html", s=scholarship, documents=documents,
                           countries=dict(COUNTRIES), degree_names=degree_text,
                           country_codes=COUNTRY_CODES,
                           days=days_left(scholarship.deadline),
                           remaining_usd=remaining_tuition_usd(scholarship),
                           over_budget=budget_warning(scholarship))
