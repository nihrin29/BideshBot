"""
Saved scholarships and comparison (FR-36, FR-37).

/saved                       the student's saved list, plus the comparison table
/saved/<id>/save   (POST)    save a scholarship
/saved/<id>/unsave (POST)    remove it from the saved list
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from matching.rules import evaluate
from models import SavedScholarship, Scholarship
from scholarships.routes import COUNTRIES, COUNTRY_CODES, DEGREES, days_left

saved_bp = Blueprint("saved", __name__, url_prefix="/saved")


@saved_bp.app_context_processor
def add_saved_ids():
    """
    Gives every template `saved_ids`: the IDs of the scholarships this student has saved,
    so the Save button can show "Saved" instead of "Save".
    """
    if not current_user.is_authenticated:
        return {"saved_ids": set()}
    return {"saved_ids": {item.scholarship_id for item in current_user.saved}}


def back_to_page():
    """Go back to the page the button was on. Only our own pages are allowed (no outside links)."""
    target = request.form.get("next", "")
    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    return redirect(url_for("saved.saved_list"))


@saved_bp.route("/<int:scholarship_id>/save", methods=["POST"])
@login_required
def save(scholarship_id):
    if db.session.get(Scholarship, scholarship_id) is None:
        abort(404)
    # Saving twice must not add a second copy.
    already = SavedScholarship.query.filter_by(user_id=current_user.id, scholarship_id=scholarship_id).first()
    if already is None:
        db.session.add(SavedScholarship(user_id=current_user.id, scholarship_id=scholarship_id))
        db.session.commit()
        flash("Scholarship saved.", "success")
    return back_to_page()


@saved_bp.route("/<int:scholarship_id>/unsave", methods=["POST"])
@login_required
def unsave(scholarship_id):
    # filter_by(user_id=...) makes sure a student can only remove their own saved items.
    item = SavedScholarship.query.filter_by(user_id=current_user.id, scholarship_id=scholarship_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Removed from your saved list.", "success")
    return back_to_page()


def compare_column(scholarship, profile):
    """Everything one column of the comparison table needs (FR-37)."""
    match = None
    if profile and profile.target_degree and profile.nationality:
        match = evaluate(profile, scholarship)
    covers = [text for text in (scholarship.tuition_coverage, scholarship.stipend) if text]
    return {
        "s": scholarship,
        "degrees": ", ".join(dict(DEGREES).get(d.strip(), d.strip())
                             for d in (scholarship.degree_levels or "").split(",") if d.strip()),
        "covers": "; ".join(covers) or "Not stated",
        "match": match,
        # Key requirements: everything except degree level (already its own row).
        "requirements": [r for r in match.rows[1:]] if match else [],
        "days": days_left(scholarship.deadline),
    }


@saved_bp.route("/")
@login_required
def saved_list():
    # Only this student's saved items (FR-36).
    items = SavedScholarship.query.filter_by(user_id=current_user.id).all()
    # Sort by soonest deadline; no deadline goes last.
    items.sort(key=lambda item: (item.scholarship.deadline is None, item.scholarship.deadline))

    # Comparison (FR-37): the ticked boxes arrive as ?compare=3&compare=7
    chosen_ids = request.args.getlist("compare", type=int)
    columns = []
    if chosen_ids:
        if not 2 <= len(chosen_ids) <= 3:
            flash("Please tick two or three scholarships to compare.", "error")
        else:
            mine = {item.scholarship_id: item.scholarship for item in items}
            if all(i in mine for i in chosen_ids):   # only the student's own saved items
                columns = [compare_column(mine[i], current_user.profile) for i in chosen_ids]
            else:
                flash("You can only compare scholarships in your saved list.", "error")

    return render_template("saved/saved.html", items=items, columns=columns, chosen_ids=chosen_ids,
                           countries=dict(COUNTRIES), country_codes=COUNTRY_CODES, days_left=days_left)
