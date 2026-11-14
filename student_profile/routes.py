"""
Pages for the academic profile (FR-08 to FR-15).

/profile         shows the saved profile
/profile/step1   step 1: degree, countries, field of study
/profile/step2   step 2: academic details, test scores and budget
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Profile, TestScore

from .forms import (FIELDS_FOR_DEGREE, TEST_FIELDS, TESTS_FOR_DEGREE, StepOneForm,
                    StepTwoForm, check_step_two)

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

# Every profile field that step 2 can fill in (used to clear old values when the degree changes).
ALL_STEP_TWO_FIELDS = sorted({name for names in FIELDS_FOR_DEGREE.values() for name in names})


@profile_bp.route("/")
@login_required
def view():
    profile = current_user.profile
    # No profile yet: start with step 1.
    if profile is None or not profile.target_degree:
        return redirect(url_for("profile.step_one"))
    return render_template("profile/view.html", profile=profile)


@profile_bp.route("/step1", methods=["GET", "POST"])
@login_required
def step_one():
    profile = current_user.profile
    form = StepOneForm()

    # When the page is first opened, fill the form with what was saved before (FR-14).
    if request.method == "GET" and profile and profile.target_degree:
        form.target_degree.data = profile.target_degree
        form.preferred_countries.data = profile.preferred_countries.split(",")
        form.field_of_study.data = profile.field_of_study

    if form.validate_on_submit():
        countries = form.preferred_countries.data
        if "Any" in countries:          # "Any" means all countries, so the others aren't needed
            countries = ["Any"]

        if profile is None:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)
        profile.target_degree = form.target_degree.data
        profile.preferred_countries = ",".join(countries)
        profile.field_of_study = form.field_of_study.data.strip()
        db.session.commit()
        return redirect(url_for("profile.step_two"))

    return render_template("profile/step1.html", form=form)


@profile_bp.route("/step2", methods=["GET", "POST"])
@login_required
def step_two():
    profile = current_user.profile
    if profile is None or not profile.target_degree:
        flash("Please complete step 1 first.", "error")
        return redirect(url_for("profile.step_one"))

    degree = profile.target_degree
    # When the page is opened, obj=profile fills the form with the saved values that have the same names.
    # When the form is sent, only the sent values are used (hidden fields keep their defaults).
    form = StepTwoForm(obj=profile) if request.method == "GET" else StepTwoForm()

    if request.method == "GET":
        # Fill in the saved test scores too.
        for test in profile.test_scores:
            short = TEST_FIELDS.get(test.test_type)
            if short:
                form[short + "_status"].data = test.status
                form[short + "_score"].data = test.score
            else:
                form.other_test_name.data = test.test_type
                form.other_test_score.data = test.score

    if request.method == "POST":
        # Run the normal checks first, then the checks that depend on the degree.
        valid = form.validate_on_submit()
        valid = check_step_two(form, degree) and valid

        if valid:
            # Only keep the fields that belong to this degree; clear the rest.
            for name in ALL_STEP_TWO_FIELDS:
                value = form[name].data if name in FIELDS_FOR_DEGREE[degree] else None
                if isinstance(value, str):
                    value = value.strip()
                setattr(profile, name, value)
            profile.nationality = form.nationality.data.strip()
            profile.yearly_budget_usd = form.yearly_budget_usd.data

            # Replace the old test scores with the new ones.
            profile.test_scores.clear()
            for test in TESTS_FOR_DEGREE[degree]:
                short = TEST_FIELDS[test]
                status = form[short + "_status"].data
                score = form[short + "_score"].data if status == "Score available" else None
                profile.test_scores.append(TestScore(test_type=test, status=status, score=score))
            if form.other_test_name.data:
                profile.test_scores.append(TestScore(test_type=form.other_test_name.data.strip(),
                                                     status="Score available",
                                                     score=form.other_test_score.data))

            db.session.commit()
            flash("Your profile has been saved.", "success")
            return redirect(url_for("profile.view"))

    tests = [(test, TEST_FIELDS[test]) for test in TESTS_FOR_DEGREE[degree]]
    return render_template("profile/step2.html", form=form, degree=degree, tests=tests)
