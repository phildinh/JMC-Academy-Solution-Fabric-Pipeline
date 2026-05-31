import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from data_generator.utils.config import (
    D365_CONTACT_LINK_RATE,
    D365_STUDENT_COUNT,
    ENROLMENT_COUNT,
    OUTPUT_BASE_PATH,
    RANDOM_SEED,
)
from data_generator.utils.fake_helpers import apply_email_casing
from data_generator.utils.logger import get_logger

logger = get_logger(__name__)

# Real JMC Academy course catalogue
_COURSES = [
    # code,           name,                                           level,              duration_terms
    ("CERT4-MUS",  "Certificate IV in Music Industry",              "Certificate IV",    2),
    ("DIP-MPROD",  "Diploma of Music Production",                   "Diploma",           4),
    ("DIP-AUDIO",  "Diploma of Audio Engineering",                  "Diploma",           4),
    ("DIP-MPERF",  "Diploma of Music Performance",                  "Diploma",           4),
    ("DIP-MSONG",  "Diploma of Songwriting",                        "Diploma",           4),
    ("BACH-MPROD", "Bachelor of Music Production",                  "Bachelor",          6),
    ("BACH-AUDIO", "Bachelor of Audio Engineering",                 "Bachelor",          6),
    ("BACH-MPERF", "Bachelor of Music Performance",                 "Bachelor",          6),
    ("BACH-MSONG", "Bachelor of Songwriting",                       "Bachelor",          6),
    ("BACH-MBIZ",  "Bachelor of Music Business",                    "Bachelor",          6),
    ("BACH-COMP",  "Bachelor of Music Composition",                 "Bachelor",          6),
    ("BACH-ELECT", "Bachelor of Electronic Music Production",       "Bachelor",          6),
    ("BACH-ENTBIZ","Bachelor of Entertainment Business",            "Bachelor",          6),
    ("BACH-FTV",   "Bachelor of Film and Television",               "Bachelor",          6),
    ("BACH-GAME",  "Bachelor of Game Design",                       "Bachelor",          6),
    ("BACH-SM",    "Bachelor of Screen and Media",                  "Bachelor",          6),
    ("BACH-JAZ",   "Bachelor of Jazz Performance",                  "Bachelor",          6),
    ("BACH-POP",   "Bachelor of Commercial Music Performance",      "Bachelor",          6),
    ("GDIP-MBIZ",  "Graduate Diploma of Music Business",            "Graduate Diploma",  4),
    ("MAST-MBIZ",  "Master of Music Business",                      "Master",            4),
]

# 6 intakes: 2023-T1 through 2025-T2
_INTAKES = [
    ("INT-01", "2023-T1", date(2023, 2, 6),  date(2023, 6, 30), 2023, "T1"),
    ("INT-02", "2023-T2", date(2023, 7, 17), date(2023, 11, 30), 2023, "T2"),
    ("INT-03", "2024-T1", date(2024, 2, 5),  date(2024, 6, 28), 2024, "T1"),
    ("INT-04", "2024-T2", date(2024, 7, 15), date(2024, 11, 29), 2024, "T2"),
    ("INT-05", "2025-T1", date(2025, 2, 3),  date(2025, 6, 27), 2025, "T1"),
    ("INT-06", "2025-T2", date(2025, 7, 14), date(2025, 11, 28), 2025, "T2"),
]

_LIFECYCLE_STATUSES = ["applied", "enrolled", "graduated", "withdrew"]
_LIFECYCLE_WEIGHTS = [0.20, 0.55, 0.15, 0.10]

# Course enrolment weights (Bachelors most popular)
_COURSE_WEIGHTS = [
    1,  # CERT4-MUS
    3, 3, 2, 2,                         # Diplomas
    8, 7, 5, 5, 5, 3, 4, 4, 3, 3, 3, 3, 4,  # Bachelors
    2, 2,                               # Postgrad
]

# Intake weights — more recent intakes have more enrolments
_INTAKE_WEIGHTS = [1, 1, 2, 2, 3, 3]

_ENROLMENT_STATUSES = ["active", "completed", "withdrawn"]
_ENROLMENT_STATUS_WEIGHTS = [0.55, 0.35, 0.10]

_AU_STATES = ["NSW", "VIC", "QLD", "SA", "WA", "ACT", "TAS", "NT"]
_STATE_WEIGHTS = [0.32, 0.25, 0.20, 0.08, 0.08, 0.04, 0.02, 0.01]


def generate_dynamics365(hs_contacts: list) -> dict:
    rng = random.Random(RANDOM_SEED + 1)   # offset seed so D365 rng diverges from HubSpot
    fake = Faker("en_AU")
    fake.seed_instance(RANDOM_SEED + 1)

    courses = _build_courses()
    intakes = _build_intakes()

    enrolled_contacts = [c for c in hs_contacts if c["lifecycle_stage"] == "enrolled"]
    num_linked = int(D365_STUDENT_COUNT * D365_CONTACT_LINK_RATE)
    linked = rng.sample(enrolled_contacts, num_linked)

    # Distribute student_numbers across years
    year_pool = ["2023"] * 75 + ["2024"] * 135 + ["2025"] * 90
    rng.shuffle(year_pool)
    year_counters: dict = {}
    def next_student_number(year: str) -> str:
        year_counters[year] = year_counters.get(year, 0) + 1
        return f"JMC{year}-{year_counters[year]:04d}"

    students = []

    # Linked students — same person as HubSpot contact
    for i, contact in enumerate(linked):
        base_email = contact["_email_base"]
        students.append({
            "student_number": next_student_number(year_pool[i]),
            "contact_id": contact["contact_id"],
            "first_name": contact["first_name"],
            "last_name": contact["last_name"],
            "email": apply_email_casing(base_email, rng),  # fresh casing — may differ from HS
            "_email_base": base_email,
            "phone": contact["phone"],
            "date_of_birth": str(_random_dob(rng)),
            "address_suburb": fake.city(),
            "address_state": rng.choices(_AU_STATES, weights=_STATE_WEIGHTS)[0],
            "lifecycle_status": rng.choices(_LIFECYCLE_STATUSES, weights=_LIFECYCLE_WEIGHTS)[0],
            "enrolment_date": str(_random_enrolment_date(rng)),
        })

    # Walk-in students — no HubSpot record
    for i in range(D365_STUDENT_COUNT - num_linked):
        base_email = fake.email().lower()
        students.append({
            "student_number": next_student_number(year_pool[num_linked + i]),
            "contact_id": None,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": apply_email_casing(base_email, rng),
            "_email_base": base_email,
            "phone": fake.phone_number(),
            "date_of_birth": str(_random_dob(rng)),
            "address_suburb": fake.city(),
            "address_state": rng.choices(_AU_STATES, weights=_STATE_WEIGHTS)[0],
            "lifecycle_status": rng.choices(_LIFECYCLE_STATUSES, weights=_LIFECYCLE_WEIGHTS)[0],
            "enrolment_date": str(_random_enrolment_date(rng)),
        })

    rng.shuffle(students)

    enrolments = _build_enrolments(students, courses, intakes, rng)

    _write_output(courses, intakes, students, enrolments)

    null_contact_count = sum(1 for s in students if s["contact_id"] is None)
    logger.info(
        f"D365: {len(courses)} courses | {len(intakes)} intakes | "
        f"{len(students)} students ({null_contact_count} walk-ins) | "
        f"{len(enrolments)} enrolments"
    )
    return {
        "courses": courses,
        "intakes": intakes,
        "students": students,
        "enrolments": enrolments,
    }


def _build_courses() -> list:
    return [
        {
            "course_id": f"COURSE-{i+1:02d}",
            "course_code": code,
            "course_name": name,
            "course_level": level,
            "duration_terms": duration,
        }
        for i, (code, name, level, duration) in enumerate(_COURSES)
    ]


def _build_intakes() -> list:
    return [
        {
            "intake_id": iid,
            "intake_code": code,
            "start_date": str(start),
            "end_date": str(end),
            "academic_year": year,
            "term": term,
        }
        for iid, code, start, end, year, term in _INTAKES
    ]


def _build_enrolments(students: list, courses: list, intakes: list, rng: random.Random) -> list:
    course_ids = [c["course_id"] for c in courses]
    intake_ids = [i["intake_id"] for i in intakes]
    intake_starts = {i["intake_id"]: date.fromisoformat(i["start_date"]) for i in intakes}
    student_numbers = [s["student_number"] for s in students]

    enrolment_id_pool = rng.sample(range(1000000, 9999999), ENROLMENT_COUNT)
    enrolments = []
    for i in range(ENROLMENT_COUNT):
        intake_id = rng.choices(intake_ids, weights=_INTAKE_WEIGHTS)[0]
        intake_start = intake_starts[intake_id]
        enrolment_date = intake_start + timedelta(days=rng.randint(-7, 14))
        status = rng.choices(_ENROLMENT_STATUSES, weights=_ENROLMENT_STATUS_WEIGHTS)[0]
        final_grade = round(rng.gauss(68, 15)) if status == "completed" else None
        if final_grade is not None:
            final_grade = max(0, min(100, final_grade))

        enrolments.append({
            "enrolment_id": f"ENR-{enrolment_id_pool[i]}",
            "student_number": rng.choice(student_numbers),
            "course_id": rng.choices(course_ids, weights=_COURSE_WEIGHTS)[0],
            "intake_id": intake_id,
            "enrolment_date": str(enrolment_date),
            "status": status,
            "final_grade": final_grade,
        })
    return enrolments


def _write_output(courses: list, intakes: list, students: list, enrolments: list) -> None:
    out = os.path.join(OUTPUT_BASE_PATH, "dynamics365")
    os.makedirs(out, exist_ok=True)

    pd.DataFrame(courses).to_csv(os.path.join(out, "courses.csv"), index=False, encoding="utf-8")
    pd.DataFrame(intakes).to_csv(os.path.join(out, "intakes.csv"), index=False, encoding="utf-8")

    # Strip internal _* keys before writing
    clean_students = [{k: v for k, v in s.items() if not k.startswith("_")} for s in students]
    pd.DataFrame(clean_students).to_csv(os.path.join(out, "students.csv"), index=False, encoding="utf-8")

    pd.DataFrame(enrolments).to_csv(os.path.join(out, "enrolments.csv"), index=False, encoding="utf-8")


def _random_dob(rng: random.Random) -> date:
    # Age 17–40 at time of enrolment
    base = date(2025, 1, 1)
    age_days = rng.randint(17 * 365, 40 * 365)
    return base - timedelta(days=age_days)


def _random_enrolment_date(rng: random.Random) -> date:
    start = date(2023, 1, 1)
    end = date(2025, 6, 30)
    return start + timedelta(days=rng.randint(0, (end - start).days))
