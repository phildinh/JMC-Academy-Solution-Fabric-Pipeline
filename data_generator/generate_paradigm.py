import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from data_generator.utils.config import (
    OUTPUT_BASE_PATH,
    PARADIGM_D365_COVERAGE_RATE,
    PARADIGM_STUDENT_COUNT,
    RANDOM_SEED,
    RESULT_COUNT,
    UNITS_PER_COURSE,
)
from data_generator.utils.fake_helpers import apply_email_casing
from data_generator.utils.logger import get_logger

logger = get_logger(__name__)

_UNIT_TOPICS = ["Foundations", "Core Skills", "Applied Practice", "Advanced Techniques", "Industry Project"]

# Grade band boundaries (Australian Higher Education standard)
def _grade_band(mark: int) -> str:
    if mark >= 85:
        return "HD"  # High Distinction
    elif mark >= 75:
        return "D"   # Distinction
    elif mark >= 65:
        return "C"   # Credit
    elif mark >= 50:
        return "P"   # Pass
    return "F"       # Fail


def generate_paradigm(d365_students: list, d365_courses: list) -> dict:
    rng = random.Random(RANDOM_SEED + 2)   # offset seed so Paradigm rng diverges
    fake = Faker("en_AU")
    fake.seed_instance(RANDOM_SEED + 2)

    units = _build_units(d365_courses)
    paradigm_students = _build_students(d365_students, rng)
    results = _build_results(paradigm_students, units, d365_courses, rng)

    _write_output(paradigm_students, units, results)

    logger.info(
        f"Paradigm: {len(paradigm_students)} students | "
        f"{len(units)} units | {len(results)} results"
    )
    return {"students": paradigm_students, "units": units, "results": results}


def _build_units(d365_courses: list) -> list:
    units = []
    unit_seq = 1
    for course in d365_courses:
        course_prefix = course["course_code"].split("-", 1)[1]  # e.g. "MPROD", "AUDIO"
        levels = ["101", "102", "103", "201", "202"]
        for i in range(UNITS_PER_COURSE):
            units.append({
                "unit_id": f"UNIT-{unit_seq:04d}",
                "unit_code": f"{course_prefix}{levels[i]}",
                "unit_name": f"{course['course_name']} - {_UNIT_TOPICS[i]}",
                "course_code": course["course_code"],
            })
            unit_seq += 1
    return units


def _build_students(d365_students: list, rng: random.Random) -> list:
    # Select ~83% of D365 students (gives ~250 of 300)
    count = min(PARADIGM_STUDENT_COUNT, len(d365_students))
    selected = rng.sample(d365_students, count)

    student_id_pool = rng.sample(range(100000, 999999), count)
    paradigm_students = []
    for i, d365_student in enumerate(selected):
        base_email = d365_student["_email_base"]
        paradigm_students.append({
            "student_code": f"P{student_id_pool[i]:06d}",
            "first_name": d365_student["first_name"],
            "last_name": d365_student["last_name"],
            "email": apply_email_casing(base_email, rng),  # fresh casing — silver resolves via lowercase match
            "_email_base": base_email,
            "_d365_student_number": d365_student["student_number"],  # internal linkage reference
        })
    return paradigm_students


def _build_results(
    paradigm_students: list,
    units: list,
    d365_courses: list,
    rng: random.Random,
) -> list:
    intake_codes = ["2023-T1", "2023-T2", "2024-T1", "2024-T2", "2025-T1", "2025-T2"]
    intake_weights = [1, 1, 2, 2, 3, 3]
    intake_start_dates = {
        "2023-T1": date(2023, 2, 6),
        "2023-T2": date(2023, 7, 17),
        "2024-T1": date(2024, 2, 5),
        "2024-T2": date(2024, 7, 15),
        "2025-T1": date(2025, 2, 3),
        "2025-T2": date(2025, 7, 14),
    }
    intake_end_dates = {
        "2023-T1": date(2023, 6, 30),
        "2023-T2": date(2023, 11, 30),
        "2024-T1": date(2024, 6, 28),
        "2024-T2": date(2024, 11, 29),
        "2025-T1": date(2025, 6, 27),
        "2025-T2": date(2025, 11, 28),
    }

    # Sample unique (student, unit) pairs — guarantees no duplicate results
    all_pairs = [
        (s["student_code"], u["unit_id"])
        for s in paradigm_students
        for u in units
    ]
    result_count = min(RESULT_COUNT, len(all_pairs))
    result_pairs = rng.sample(all_pairs, result_count)

    result_id_pool = rng.sample(range(1000000, 9999999), result_count)
    results = []
    for i, (student_code, unit_id) in enumerate(result_pairs):
        intake_code = rng.choices(intake_codes, weights=intake_weights)[0]
        intake_start = intake_start_dates[intake_code]
        intake_end = intake_end_dates[intake_code]
        result_date = intake_start + timedelta(
            days=rng.randint(int((intake_end - intake_start).days * 0.8), (intake_end - intake_start).days)
        )
        mark = max(0, min(100, round(rng.gauss(70, 15))))
        results.append({
            "result_id": f"RES-{result_id_pool[i]}",
            "student_code": student_code,
            "unit_id": unit_id,
            "intake_code": intake_code,
            "mark": mark,
            "grade": _grade_band(mark),
            "result_date": str(result_date),
        })
    return results


def _write_output(paradigm_students: list, units: list, results: list) -> None:
    out = os.path.join(OUTPUT_BASE_PATH, "paradigm")
    os.makedirs(out, exist_ok=True)

    clean_students = [{k: v for k, v in s.items() if not k.startswith("_")} for s in paradigm_students]
    pd.DataFrame(clean_students).to_csv(os.path.join(out, "students.csv"), index=False, encoding="utf-8")
    pd.DataFrame(units).to_csv(os.path.join(out, "units.csv"), index=False, encoding="utf-8")
    pd.DataFrame(results).to_csv(os.path.join(out, "results.csv"), index=False, encoding="utf-8")
