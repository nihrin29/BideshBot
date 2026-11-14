"""
The "Your matches" page (FR-16 to FR-24).

/matches   results for the logged-in student, in three tabs
"""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Scholarship
from scholarships.routes import COUNTRIES, COUNTRY_CODES, FUNDING_TYPES, days_left, visible_scholarships

from .rules import CLOSE, MATCH_SETTINGS, MEETS, VERIFY, match_scholarships

matching_bp = Blueprint("matching", __name__, url_prefix="/matches")

# Short names used in the address bar for each tab, e.g. /matches?tab=close
TAB_KEYS = {"meets": MEETS, "close": CLOSE, "verify": VERIFY}

# FR-22: how many close matches to show before "View more".
FIRST_CLOSE_MATCHES = 5


@matching_bp.route("/")
@login_required
def results():
    profile = current_user.profile
    # Matching needs a finished profile (step 2 sets the nationality).
    if profile is None or not profile.target_degree or not profile.nationality:
        flash("Please complete your profile first so we can match you.", "error")
        return redirect(url_for("profile.step_one"))

    # Filters (FR-16). Country "" means the countries in the student's profile.
    country = request.args.get("country", "")
    funding = request.args.get("funding", "")
    field = request.args.get("field", "").strip()
    sort = request.args.get("sort", "best")          # FR-23: "best" (default) or "deadline"
    tab_key = request.args.get("tab", "meets")
    show_all = request.args.get("more") == "1"
    if tab_key not in TAB_KEYS:
        tab_key = "meets"

    # Only published, not-expired scholarships are matched (FR-26).
    query = visible_scholarships()
    preferred = [c for c in (profile.preferred_countries or "").split(",") if c]
    if country == "":
        if preferred and "Any" not in preferred:
            query = query.filter(Scholarship.country.in_(preferred))
    elif country != "all":
        query = query.filter(Scholarship.country == country)
    if funding:
        query = query.filter(Scholarship.funding_type == funding)
    if field:
        query = query.filter(Scholarship.fields.ilike(f"%{field}%") | Scholarship.fields.ilike("%any%"))
    scholarships = query.all()

    # FR-24: if something goes wrong, show a friendly message instead of an error page.
    try:
        tabs = match_scholarships(profile, scholarships)
    except Exception:
        current_app.logger.exception("Matching failed")
        return render_template("matching/results.html", failed=True, profile=profile)

    # FR-23: sort by soonest deadline instead of best match (no deadline goes last).
    if sort == "deadline":
        for items in tabs.values():
            items.sort(key=lambda r: (r.scholarship.deadline is None, r.scholarship.deadline))

    shown = tabs[TAB_KEYS[tab_key]]
    hidden_count = 0
    if tab_key == "close" and not show_all and len(shown) > FIRST_CLOSE_MATCHES:
        hidden_count = len(shown) - FIRST_CLOSE_MATCHES
        shown = shown[:FIRST_CLOSE_MATCHES]

    return render_template("matching/results.html", failed=False, profile=profile, tabs=tabs,
                           tab_keys=TAB_KEYS, tab_key=tab_key, shown=shown, hidden_count=hidden_count,
                           total=len(scholarships), country=country, funding=funding, field=field,
                           sort=sort, countries=COUNTRIES, funding_types=FUNDING_TYPES,
                           country_codes=COUNTRY_CODES, days_left=days_left,
                           min_days=MATCH_SETTINGS["close_match_min_days"])
