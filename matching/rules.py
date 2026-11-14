"""
The matching rules (FR-16 to FR-21, SRS section 7.2).

This file is plain Python: no Flask, no AI. It takes a student's profile and a list of
scholarships and works out, rule by rule, which tab each scholarship belongs in.

Every requirement gets one of four results:
    Met, Not met, Unknown (we can't tell) or Not applicable (doesn't apply to this student).
Unknown is never treated as a pass or a fail (SRS 7.2).
"""

from datetime import date

MET, NOT_MET, UNKNOWN, NOT_APPLICABLE = "Met", "Not met", "Unknown", "Not applicable"

# The three tabs (FR-17).
MEETS, CLOSE, VERIFY = "Meets recorded criteria", "Close match", "Needs verification"

# All settings in one place so they can be changed after testing (SRS 7.2: "configurable").
MATCH_SETTINGS = {
    "close_match_min_days": 30,   # a close match needs at least this many days before the deadline
    "max_soft_misses": 2,         # a close match can miss at most this many soft criteria
    # How far below the requirement still counts as "close" for each test.
    "test_margins": {"IELTS": 0.5, "TOEFL iBT": 10, "GRE": 5, "SAT": 0},
    # Grade margins per grading scale. Only the 4.00 scale has a margin in the SRS,
    # so a missed grade on any other scale is never a close match.
    "grade_margins": {4.0: 0.30},
    # Not given in the SRS: my own starting value, to be reviewed during testing.
    "work_experience_margin": 1.0,
}

TESTS = ["IELTS", "TOEFL iBT", "GRE", "SAT"]
TESTS_FOR_DEGREE = {"Bachelor": ["IELTS", "TOEFL iBT", "SAT"],
                    "Master": ["IELTS", "TOEFL iBT", "GRE"],
                    "PhD": ["IELTS", "TOEFL iBT", "GRE"]}

# Which profile result is used for each grade criterion, and which degrees it applies to.
GRADES = {
    "CGPA": ("bachelor_cgpa", "bachelor_scale", ["Master", "PhD"]),
    "Master CGPA": ("master_cgpa", "master_scale", ["PhD"]),
    "HSC result": ("higher_secondary_result", "higher_secondary_scale", ["Bachelor"]),
}

DEGREE_NAMES = {"Bachelor": "Bachelor's", "Master": "Master's", "PhD": "PhD"}


def num(value):
    """6.0 -> "6", 3.45 -> "3.45" (no pointless .0)."""
    return f"{value:g}"


def years(value):
    """1 -> "1 year", 2.5 -> "2.5 years"."""
    return f"{num(value)} year" + ("" if value == 1 else "s")


def as_number(text):
    """Turn "6.5" into 6.5. Returns None if the text is not a number."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


class Row:
    """One line of the breakdown table: requirement, required value, student's value, result (FR-18)."""

    def __init__(self, criterion, required, yours, result, is_hard=False, gap=None, margin=None):
        self.criterion = criterion
        self.required = required
        self.yours = yours
        self.result = result
        self.is_hard = is_hard
        self.gap = gap            # how far below the requirement the student is (only for Not met)
        self.margin = margin      # how big a gap still counts as "close" (None = never close)
        self.suggestion = None    # improvement tip, filled in for close matches (FR-20)
        # Which test/criterion the suggestion is about (differs only for "IELTS or TOEFL" rows).
        self.tip_name = criterion
        self.tip_required = required
        self.not_taken = False    # True when a test was never taken

    def within_margin(self):
        return self.gap is not None and self.margin is not None and self.gap <= self.margin

    def gap_size(self):
        """Gap as a share of the margin, so IELTS and TOEFL gaps can be compared when ranking."""
        if self.gap is None:
            return 0
        return self.gap / self.margin if self.margin else self.gap


def compare_number(criterion, required, yours, margin, yours_text=None):
    """Compare a student's number with a minimum requirement."""
    if yours >= required:
        return Row(criterion, num(required), yours_text or num(yours), MET)
    gap = round(required - yours, 2)
    return Row(criterion, num(required), yours_text or num(yours), NOT_MET, gap=gap, margin=margin)


def check_test(profile, requirement):
    """IELTS, TOEFL iBT, GRE or SAT: the student's score must be at least the required score."""
    test = requirement.criterion
    required = as_number(requirement.value)
    if test not in TESTS_FOR_DEGREE[profile.target_degree]:
        return Row(test, requirement.value, "–", NOT_APPLICABLE)
    score = next((t for t in profile.test_scores if t.test_type == test), None)
    if required is None:
        return Row(test, "Not clear", "–", UNKNOWN)
    if score is None or score.status != "Score available" or score.score is None:
        # Missing profile data -> Unknown (never a fail).
        row = Row(test, num(required), score.status if score else "Not entered", UNKNOWN)
        # Remember if the test was not taken at all (used for "IELTS or TOEFL" below).
        row.not_taken = score is None or score.status == "Not taken"
        return row
    return compare_number(test, required, score.score, MATCH_SETTINGS["test_margins"].get(test))


def check_grade(profile, requirement):
    """CGPA-type results. Only compared when both use the same grading scale (SRS 7.2)."""
    result_field, scale_field, degrees = GRADES[requirement.criterion]
    name = requirement.criterion
    if profile.target_degree not in degrees:
        return Row(name, requirement.value, "–", NOT_APPLICABLE)
    required, scale = as_number(requirement.value), requirement.grading_scale
    yours, your_scale = getattr(profile, result_field), getattr(profile, scale_field)
    if required is None or scale is None:
        return Row(name, "Not clear", "–", UNKNOWN)
    required_text = f"{required:.2f} / {scale:.2f}"
    if yours is None or your_scale is None:
        return Row(name, required_text, "Not entered", UNKNOWN)
    yours_text = f"{yours:.2f} / {your_scale:.2f}"
    if your_scale != scale:
        # Different scales: no conversion is assumed, so we can't tell.
        return Row(name, required_text, yours_text + " (different scale)", UNKNOWN)
    row = compare_number(name, required, yours, MATCH_SETTINGS["grade_margins"].get(scale), yours_text)
    row.required = row.tip_required = required_text
    return row


def check_work_experience(profile, requirement):
    required = as_number(requirement.value)
    if profile.target_degree == "Bachelor":
        return Row("Work experience", requirement.value, "–", NOT_APPLICABLE)
    if required is None:
        return Row("Work experience", "Not clear", "–", UNKNOWN)
    yours = profile.work_experience_years
    if yours is None:
        return Row("Work experience", years(required), "Not entered", UNKNOWN)
    row = compare_number("Work experience", required, yours, MATCH_SETTINGS["work_experience_margin"],
                         years(yours))
    row.required = row.tip_required = years(required)
    return row


def check_list(name, allowed_text, student_value):
    """
    Nationality or restricted field: the requirement is a comma-separated list, or "Any".
    Met if the student's value is in the list, otherwise Not met.
    """
    if not student_value:
        return Row(name, allowed_text, "Not entered", UNKNOWN)
    allowed = [item.strip().lower() for item in allowed_text.split(",") if item.strip()]
    mine = student_value.strip().lower()
    if "any" in allowed or any(item in mine or mine in item for item in allowed):
        return Row(name, allowed_text, student_value, MET)
    return Row(name, allowed_text, student_value, NOT_MET)


def check_requirement(profile, requirement):
    """Work out the result of one requirement for this student."""
    name = requirement.criterion
    if requirement.is_unknown or requirement.value is None:
        # FR-54: the official page wasn't clear, so we can't decide.
        row = Row(name, "Unknown – check the official page", "–", UNKNOWN)
    elif name in TESTS:
        row = check_test(profile, requirement)
    elif name in GRADES:
        row = check_grade(profile, requirement)
    elif name == "Work experience":
        row = check_work_experience(profile, requirement)
    elif name == "Nationality":
        row = check_list(name, requirement.value, profile.nationality)
    elif name == "Field":
        row = check_list("Field of study", requirement.value, profile.field_of_study)
    else:
        # A written rule (e.g. "Nominated by your school") that a computer can't check.
        row = Row(name, requirement.value, "Check yourself", UNKNOWN)
    row.is_hard = requirement.is_hard
    return row


def combine_alternatives(rows):
    """
    Alternatives (same alternative_group, e.g. IELTS or TOEFL) count as ONE criterion (SRS 7.2):
    1. Met if any one is met.
    2. Otherwise Unknown if one could still be met (e.g. TOEFL "Awaiting result").
    3. Otherwise Not met, using the closest miss (a test that was never taken is ignored here,
       so "IELTS 6.0, TOEFL not taken" shows the IELTS gap).
    4. Otherwise Unknown (nothing taken yet).
    """
    met = [r for r in rows if r.result == MET]
    unknown = [r for r in rows if r.result == UNKNOWN and not r.not_taken]
    missed = [r for r in rows if r.result == NOT_MET]
    not_taken = [r for r in rows if r.result == UNKNOWN and r.not_taken]
    if met:
        best = met[0]
    elif unknown:
        best = unknown[0]
    elif missed:
        best = min(missed, key=Row.gap_size)   # the closest miss
    elif not_taken:
        best = not_taken[0]
    else:
        best = rows[0]                         # all Not applicable
    combined = Row(" or ".join(r.criterion for r in rows), " or ".join(r.required for r in rows),
                   best.yours, best.result,
                   is_hard=any(r.is_hard for r in rows), gap=best.gap, margin=best.margin)
    if best.result in (MET, NOT_MET):
        combined.yours = f"{best.criterion} {best.yours}"
    # The suggestion talks about the closest alternative, e.g. "Retake IELTS to reach 6.5".
    combined.tip_name, combined.tip_required = best.tip_name, best.tip_required
    return combined


def suggestion_for(row, days):
    """A rule-based improvement tip for one missed criterion (FR-20). No AI."""
    name, required = row.tip_name, row.tip_required
    days_text = f"{days} days until the deadline"
    if name in TESTS:
        return f"Retake {name} to reach at least {required} – {days_text}."
    if name == "Work experience":
        return f"Gain more work experience to reach {required} – {days_text}."
    if name in GRADES:
        return (f"Your result is {num(row.gap)} below the minimum. Ask the provider whether "
                f"other evidence (e.g. strong test scores) can be considered – {days_text}.")
    return f"Check how to meet this requirement on the official page – {days_text}."


class MatchResult:
    """The result for one scholarship: which tab, the breakdown rows, and why."""

    def __init__(self, scholarship, rows, tab, reason=None, days=None):
        self.scholarship = scholarship
        self.rows = rows
        self.tab = tab            # one of the three tabs, or None when not shown
        self.reason = reason      # why it is excluded or not shown
        self.days = days
        self.missed = [r for r in rows if r.result == NOT_MET]

    def rank_key(self):
        """SRS 7.2 ranking: fewest misses, then smallest gap, then soonest known deadline."""
        deadline = self.scholarship.deadline
        return (len(self.missed), sum(r.gap_size() for r in self.missed),
                deadline is None, deadline or date.max)


def evaluate(profile, scholarship, today=None):
    """Check one scholarship against one profile and decide its tab."""
    today = today or date.today()
    days = (scholarship.deadline - today).days if scholarship.deadline else None

    # 1. Degree level is always a hard criterion, taken from the scholarship itself.
    levels = [d.strip() for d in (scholarship.degree_levels or "").split(",") if d.strip()]
    required_text = ", ".join(DEGREE_NAMES.get(d, d) for d in levels) or "Not stated"
    yours_text = DEGREE_NAMES.get(profile.target_degree, profile.target_degree)
    degree_result = UNKNOWN if not levels else (MET if profile.target_degree in levels else NOT_MET)
    rows = [Row("Degree level", required_text, yours_text, degree_result, is_hard=True)]

    # 2. Every recorded requirement; alternatives are combined into one row.
    groups = {}
    for requirement in scholarship.requirements:
        row = check_requirement(profile, requirement)
        if requirement.alternative_group:
            groups.setdefault(requirement.alternative_group, []).append(row)
        else:
            rows.append(row)
    rows += [combine_alternatives(group) for group in groups.values()]

    # 3. Hard criteria first: a confirmed failure excludes the scholarship (FR-21).
    hard_fails = [r for r in rows if r.is_hard and r.result == NOT_MET]
    if hard_fails:
        reasons = "; ".join(f"{r.criterion}: required {r.required}, yours {r.yours}" for r in hard_fails)
        return MatchResult(scholarship, rows, None, reason=reasons, days=days)

    missed = [r for r in rows if r.result == NOT_MET]
    unknown = [r for r in rows if r.result == UNKNOWN]
    hard_unknown = [r for r in unknown if r.is_hard]

    # 4. Nothing missed: Meets (all known) or Needs verification (something unknown).
    if not missed:
        return MatchResult(scholarship, rows, VERIFY if unknown else MEETS, days=days)

    # 5. Close match: few small gaps and enough time to fix them (FR-19).
    small_gaps = len(missed) <= MATCH_SETTINGS["max_soft_misses"] and all(r.within_margin() for r in missed)
    enough_time = days is not None and days >= MATCH_SETTINGS["close_match_min_days"]
    if small_gaps and enough_time:
        for r in missed:
            r.suggestion = suggestion_for(r, days)
        # A hard criterion we couldn't check means it can't be called a close match yet.
        return MatchResult(scholarship, rows, VERIFY if hard_unknown else CLOSE, days=days)

    # 6. Too many or too big gaps, or too little time: not shown.
    if not small_gaps:
        reason = "More than two criteria missed, or a gap that is too big"
    else:
        reason = f"Fewer than {MATCH_SETTINGS['close_match_min_days']} days left (or no confirmed deadline)"
    return MatchResult(scholarship, rows, None, reason=reason, days=days)


def match_scholarships(profile, scholarships, today=None):
    """
    Check every scholarship and sort them into the three tabs (FR-17).
    Returns a dict: tab name -> list of MatchResult, ranked best first (SRS 7.2, NFR-23).
    """
    tabs = {MEETS: [], CLOSE: [], VERIFY: []}
    for scholarship in scholarships:
        result = evaluate(profile, scholarship, today)
        if result.tab:
            tabs[result.tab].append(result)
    for results in tabs.values():
        results.sort(key=MatchResult.rank_key)
    return tabs
