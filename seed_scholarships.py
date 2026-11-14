"""
Adds a few real scholarships to the database so the list and details pages have something to show.

STARTER DATA ONLY: the real collection job (Card 8) will replace this.
Every fact below was checked on the official page on 15 Nov 2026.
Anything the official page did not say is left empty (shown as "Not stated" or "Unknown"), never guessed.

Run it with:  python seed_scholarships.py
Running it again does not add duplicates (scholarships with the same title are skipped).

Requirement values the matching rules can check (Card 5):
    tests and grades -> a number ("6.5"), work experience -> years ("2"),
    nationality / field -> a comma-separated list or "Any".
Anything written in words is shown to the student as "Check yourself".
"""

from datetime import date, datetime

from app import app
from extensions import db
from models import Requirement, Scholarship

# The day the facts were checked on the official pages.
CHECKED_ON = datetime(2026, 11, 15)

SCHOLARSHIPS = [
    {
        "title": "Knight-Hennessy Scholars",
        "provider": "Stanford University",
        "country": "USA",
        "degree_levels": "Master,PhD",
        "fields": "Any full-time Stanford graduate degree",
        "summary": "Funding for up to three years for any graduate degree at Stanford University.",
        "funding_type": "Full funding",
        "tuition_coverage": "Full tuition and associated fees",
        "stipend": "Stipend for living and academic expenses (room and board, books, academic supplies)",
        "other_benefits": "Travel stipend for one economy round trip to Stanford each year",
        "deadline": date(2026, 10, 6),
        "application_url": "https://apply.knight-hennessy.stanford.edu",
        "source_url": "https://knight-hennessy.stanford.edu/admission/before-you-apply/eligibility",
        "requirements": [
            ("Bachelor's degree", True, "Earned in January 2020 or later"),
            ("Stanford admission", True, "Apply to, be accepted by and enrol in a full-time Stanford graduate programme"),
            ("English test", True, None),   # not stated on the page -> Unknown
        ],
    },
    {
        "title": "Commonwealth Master's Scholarships",
        "provider": "Commonwealth Scholarship Commission in the UK",
        "country": "UK",
        "degree_levels": "Master",
        "fields": "Any one-year taught Master's (not MBA)",
        "summary": "One-year taught Master's in the UK for students from eligible Commonwealth countries "
                   "who could not afford UK study otherwise.",
        "funding_type": "Full funding",
        "tuition_coverage": "Full tuition fees",
        "stipend": "GBP 1,712 per month (GBP 2,000 per month in the London area)",
        "other_benefits": "Return airfare, study travel grant, child allowance for single-parent scholars",
        "not_covered": "Airfare for dependants",
        "required_documents": "Passport or national ID card\n"
                              "Full transcripts of all higher education\n"
                              "At least two signed references",
        "deadline": date(2026, 10, 20),
        "application_url": "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-masters-scholarships/",
        "source_url": "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-masters-scholarships/",
        "requirements": [
            # Only Bangladesh was checked on the official eligible-country list so far.
            ("Nationality", True, "Bangladesh"),
            ("Bachelor's degree", True, "Upper second-class (2:1), or 2:2 plus a relevant postgraduate qualification"),
            ("Nomination", True, "Apply through a national nominating agency, not directly"),
            ("Return home", True, "Commit to returning home after the award"),
        ],
    },
    {
        "title": "DAAD EPOS – Development-Related Postgraduate Courses",
        "provider": "DAAD",
        "country": "Germany",
        "degree_levels": "Master",
        "fields": "Development-related subjects (selected courses)",
        "summary": "Master's study on development-related courses at German universities for "
                   "professionals from developing countries.",
        "funding_type": None,            # the page does not say whether tuition is covered
        "stipend": "EUR 992 per month for graduates",
        "other_benefits": "Health, accident and liability insurance; travel allowance; "
                          "rent subsidy and family allowance in some cases",
        "required_documents": "Signed checklist\nEPOS application form\nCV (Europass format preferred)\n"
                              "Letter of motivation\nLetter of recommendation from current employer\n"
                              "Certificates of employment (at least two years)\nIELTS or TOEFL certificate\n"
                              "Degree certificates\nFull transcript of records",
        "deadline": None,                # set by each course
        "application_url": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/?detail=50076777",
        "source_url": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/?detail=50076777",
        "requirements": [
            ("Bachelor's degree", True, "Usually four years, related subject, normally not older than six years"),
            ("Academic results", True, "Upper third of the class"),
            ("Work experience", True, "2"),   # years, after the Bachelor's degree
            ("Nationality", True, None),  # country list not checked -> Unknown
        ],
    },
    {
        "title": "Deutschlandstipendium",
        "provider": "German universities with private sponsors and the Federal Government",
        "country": "Germany",
        "degree_levels": "Bachelor,Master",
        "fields": "Any",
        "summary": "Merit scholarship given by German universities to students of all nationalities, "
                   "without looking at income.",
        "funding_type": "Partial funding",
        "stipend": "EUR 300 per month (EUR 150 from private sponsors, EUR 150 from the Federal Government)",
        "deadline": None,                # each university sets its own
        "application_url": "https://www.deutschlandstipendium.de/de/english-1700.html",
        "source_url": "https://www.deutschlandstipendium.de/de/english-1700.html",
        "requirements": [
            ("Nationality", True, "Any"),     # open to all nationalities
            ("Selection", False, "Academic achievement, social commitment and personal achievements"),
        ],
    },
    {
        "title": "International Major Entrance Scholarship (IMES)",
        "provider": "University of British Columbia",
        "country": "Canada",
        "degree_levels": "Bachelor",
        "fields": "Any",
        "summary": "Entrance scholarship for outstanding international students starting an "
                   "undergraduate degree at UBC. Applicants are considered automatically.",
        "funding_type": "Partial funding",
        "tuition_coverage": "CAD 10,000 to 25,000 per year (2027/2028), renewable for up to three more years",
        "deadline": date(2026, 12, 2),   # apply to UBC by this date to be considered
        "application_url": "https://you.ubc.ca/applying-ubc/dates-deadlines/",
        "source_url": "https://you.ubc.ca/financial-planning/scholarships-awards-international-students/international-entrance-scholarships/",
        "requirements": [
            ("Entry route", True, "New to UBC, entering directly from secondary school"),
            ("Study permit", True, "Studying in Canada on a study permit"),
            ("Selection", False, "Exceptional academic achievement and extracurricular involvement"),
        ],
    },
    {
        "title": "Lester B. Pearson International Scholarship",
        "provider": "University of Toronto",
        "country": "Canada",
        "degree_levels": "Bachelor",
        "fields": "Any first-entry undergraduate programme",
        "summary": "Covers tuition, books, fees and residence for four years at the University of Toronto. "
                   "About 37 scholars are named each year.",
        "funding_type": "Full funding",
        "tuition_coverage": "Full tuition for four years",
        "other_benefits": "Books, incidental fees and full residence support for four years",
        "deadline": date(2026, 11, 6),
        "application_url": "https://future.utoronto.ca/pearson/about/",
        "source_url": "https://future.utoronto.ca/pearson/about/",
        "requirements": [
            ("Nomination", True, "Nominated by your current secondary school"),
            ("School year", True, "Final year of secondary school in 2026/2027, or graduated in June 2026 or later"),
            ("Student type", True, "International student needing a study permit"),
        ],
    },
]


def seed():
    with app.app_context():
        added = 0
        for data in SCHOLARSHIPS:
            data = dict(data)                      # copy, so the list above is not changed
            rules = data.pop("requirements")
            if Scholarship.query.filter_by(title=data["title"]).first():
                continue                           # already in the database
            scholarship = Scholarship(**data, status="Published", last_collected=CHECKED_ON)
            for criterion, is_hard, value in rules:
                scholarship.requirements.append(Requirement(
                    criterion=criterion, is_hard=is_hard, value=value,
                    is_unknown=value is None))     # no value on the official page -> Unknown
            db.session.add(scholarship)
            added += 1
        db.session.commit()
        print(f"Added {added} scholarship(s).")


if __name__ == "__main__":
    seed()
