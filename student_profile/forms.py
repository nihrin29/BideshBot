"""
Forms for the two-step academic profile (FR-08 to FR-15).

Step 1 asks what the student wants to study and where.
Step 2 asks for academic details. Which fields are required depends on the
degree chosen in step 1, so those checks are done in check_step_two() below.
"""

from flask_wtf import FlaskForm
from wtforms import (FloatField, IntegerField, RadioField, SelectField,
                     SelectMultipleField, StringField, SubmitField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget

DEGREE_CHOICES = [("Bachelor", "Bachelor's"), ("Master", "Master's"), ("PhD", "PhD")]
COUNTRY_CHOICES = [("USA", "USA"), ("UK", "UK"), ("Germany", "Germany"), ("Canada", "Canada"), ("Any", "Any")]

# Grading scales a result can be out of. coerce=float turns "4.0" into the number 4.0.
SCALE_CHOICES = [(4.0, "4.00"), (5.0, "5.00"), (10.0, "10"), (100.0, "100 (percentage)")]

STATUS_CHOICES = [("Not taken", "Not taken"), ("Awaiting result", "Awaiting result"),
                  ("Score available", "Score available")]

# FR-12: only the tests relevant to the chosen degree are shown.
# Each test name is linked to the short name used for its form fields (e.g. "ielts_status").
TEST_FIELDS = {"IELTS": "ielts", "TOEFL iBT": "toefl", "GRE": "gre", "SAT": "sat"}
TESTS_FOR_DEGREE = {
    "Bachelor": ["IELTS", "TOEFL iBT", "SAT"],
    "Master": ["IELTS", "TOEFL iBT", "GRE"],
    "PhD": ["IELTS", "TOEFL iBT", "GRE"],
}

# FR-13: the lowest and highest possible score of each test.
TEST_LIMITS = {"IELTS": (0, 9), "TOEFL iBT": (0, 120), "GRE": (260, 340), "SAT": (400, 1600)}

# Profile fields used by each degree level (FR-09, FR-10, FR-11).
FIELDS_FOR_DEGREE = {
    "Bachelor": ["school_qualification", "secondary_result", "secondary_scale",
                 "higher_secondary_result", "higher_secondary_scale"],
    "Master": ["bachelor_cgpa", "bachelor_scale", "institution", "bachelor_field",
               "graduation_year", "work_experience_years"],
    "PhD": ["bachelor_cgpa", "bachelor_scale", "master_cgpa", "master_scale", "research_area",
            "publications", "research_experience_years", "work_experience_years"],
}

# Fields that must be filled in for each degree level.
REQUIRED_FOR_DEGREE = {
    "Bachelor": ["secondary_result", "higher_secondary_result"],
    "Master": ["bachelor_cgpa", "institution", "bachelor_field", "graduation_year"],
    "PhD": ["bachelor_cgpa", "master_cgpa", "research_area"],
}

# Each result and the scale it is measured on, so we can check result <= scale.
RESULT_AND_SCALE = [
    ("secondary_result", "secondary_scale"),
    ("higher_secondary_result", "higher_secondary_scale"),
    ("bachelor_cgpa", "bachelor_scale"),
    ("master_cgpa", "master_scale"),
]


class MultiCheckboxField(SelectMultipleField):
    """A list of checkboxes where the student can tick more than one (used for countries)."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class StepOneForm(FlaskForm):
    target_degree = RadioField("Which degree are you applying for?", choices=DEGREE_CHOICES,
                               validators=[DataRequired(message="Please choose a degree.")])
    preferred_countries = MultiCheckboxField("Where would you like to study?", choices=COUNTRY_CHOICES,
                                             validators=[DataRequired(message="Please choose at least one country.")])
    field_of_study = StringField("Intended field of study", validators=[
        DataRequired(message="Please enter your field of study."), Length(max=100)])
    submit = SubmitField("Next: academic details →")


def optional_number(label, minimum=0, maximum=None, whole=False):
    """A number box that may be left empty, but can't be below `minimum` (FR-13: no negative values)."""
    field_type = IntegerField if whole else FloatField
    return field_type(label, validators=[
        Optional(),
        NumberRange(min=minimum, max=maximum, message=f"Must be {minimum} or more."
                    if maximum is None else f"Must be between {minimum} and {maximum}."),
    ])


class StepTwoForm(FlaskForm):
    # Bachelor's applicants (FR-09)
    school_qualification = SelectField("School qualification", choices=[
        ("SSC/HSC", "SSC and HSC"), ("O/A-Level", "O-Level and A-Level"), ("Other", "Other equivalent")],
        default="SSC/HSC")
    secondary_result = optional_number("SSC / O-Level result")
    secondary_scale = SelectField("Out of", choices=SCALE_CHOICES, coerce=float, default=5.0)
    higher_secondary_result = optional_number("HSC / A-Level result")
    higher_secondary_scale = SelectField("Out of", choices=SCALE_CHOICES, coerce=float, default=5.0)

    # Master's and PhD applicants (FR-10, FR-11)
    bachelor_cgpa = optional_number("Bachelor's CGPA")
    bachelor_scale = SelectField("Out of", choices=SCALE_CHOICES, coerce=float, default=4.0)
    institution = StringField("University", validators=[Optional(), Length(max=150)])
    bachelor_field = StringField("Department / field", validators=[Optional(), Length(max=100)])
    graduation_year = optional_number("Graduation year (actual or expected)", 1980, 2035, whole=True)
    work_experience_years = optional_number("Work experience (years)")

    # PhD applicants only (FR-11)
    master_cgpa = optional_number("Master's CGPA")
    master_scale = SelectField("Out of", choices=SCALE_CHOICES, coerce=float, default=4.0)
    research_area = StringField("Research area", validators=[Optional(), Length(max=150)])
    publications = optional_number("Number of publications", whole=True)
    research_experience_years = optional_number("Research experience (years)")

    # Everyone (FR-14): pre-filled as Bangladesh, but can be changed.
    nationality = StringField("Nationality", default="Bangladesh", validators=[
        DataRequired(message="Please enter your nationality."), Length(max=50)])

    # Test scores (FR-12): a status and, if available, a score.
    # The defaults matter: tests that are not shown for a degree still need a valid value.
    ielts_status = SelectField("IELTS", choices=STATUS_CHOICES, default="Not taken")
    ielts_score = FloatField("IELTS score", validators=[Optional()])
    toefl_status = SelectField("TOEFL iBT", choices=STATUS_CHOICES, default="Not taken")
    toefl_score = FloatField("TOEFL iBT score", validators=[Optional()])
    gre_status = SelectField("GRE", choices=STATUS_CHOICES, default="Not taken")
    gre_score = FloatField("GRE score", validators=[Optional()])
    sat_status = SelectField("SAT", choices=STATUS_CHOICES, default="Not taken")
    sat_score = FloatField("SAT score", validators=[Optional()])
    other_test_name = StringField("Other test name", validators=[Optional(), Length(max=50)])
    other_test_score = FloatField("Score", validators=[Optional()])

    # FR-15: optional yearly budget in US dollars.
    yearly_budget_usd = optional_number("Most I can pay for tuition per year (USD)")

    submit = SubmitField("Save profile")


def add_error(field, message):
    """Show an error message under a form field."""
    field.errors = list(field.errors) + [message]


def check_step_two(form, degree):
    """
    Extra checks that depend on the chosen degree (FR-09 to FR-13).
    Returns True if everything is fine, otherwise adds error messages and returns False.
    """
    ok = True

    # 1. Required fields for this degree level.
    for name in REQUIRED_FOR_DEGREE[degree]:
        if form[name].data in (None, ""):
            add_error(form[name], "This field is required.")
            ok = False

    # 2. A result can't be higher than its grading scale (e.g. CGPA 4.5 out of 4.00).
    for result_name, scale_name in RESULT_AND_SCALE:
        if result_name not in FIELDS_FOR_DEGREE[degree]:
            continue
        result, scale = form[result_name].data, form[scale_name].data
        if result is not None and result > scale:
            add_error(form[result_name], f"Can't be more than the scale ({scale:g}).")
            ok = False

    # 3. Test scores must be inside the valid range for that test.
    for test in TESTS_FOR_DEGREE[degree]:
        short = TEST_FIELDS[test]
        status, score = form[short + "_status"].data, form[short + "_score"]
        if status != "Score available":
            continue
        if score.data is None:
            add_error(score, "Please enter your score.")
            ok = False
            continue
        low, high = TEST_LIMITS[test]
        if not low <= score.data <= high:
            add_error(score, f"{test} must be between {low} and {high}.")
            ok = False
        elif test == "IELTS" and (score.data * 2) % 1 != 0:
            add_error(score, "IELTS goes up in steps of 0.5 (e.g. 6.0, 6.5).")
            ok = False

    # 4. Another test needs both a name and a score.
    if form.other_test_name.data and form.other_test_score.data is None:
        add_error(form.other_test_score, "Please enter the score.")
        ok = False
    if form.other_test_score.data is not None and not form.other_test_name.data:
        add_error(form.other_test_name, "Please enter the test name.")
        ok = False

    return ok
