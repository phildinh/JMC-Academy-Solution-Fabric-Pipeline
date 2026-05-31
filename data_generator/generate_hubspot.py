import json
import os
import random
from datetime import date, timedelta

from faker import Faker

from data_generator.utils.config import (
    D365_CONTACT_LINK_RATE,
    D365_STUDENT_COUNT,
    HUBSPOT_ACTIVITY_COUNT,
    HUBSPOT_CONTACT_COUNT,
    OUTPUT_BASE_PATH,
    RANDOM_SEED,
)
from data_generator.utils.fake_helpers import apply_email_casing
from data_generator.utils.logger import get_logger

logger = get_logger(__name__)

# 10 marketing sources with realistic uneven weights
_SOURCES = [
    ("MS-01", "Paid Social – Facebook",    "Paid Social",    0.18),
    ("MS-02", "Paid Social – Instagram",   "Paid Social",    0.12),
    ("MS-03", "Organic Search – Google",   "Organic Search", 0.20),
    ("MS-04", "Organic Search – Bing",     "Organic Search", 0.05),
    ("MS-05", "Referral",                  "Referral",       0.15),
    ("MS-06", "Email Campaign",            "Email",          0.10),
    ("MS-07", "Paid Search – Google Ads",  "Paid Search",    0.08),
    ("MS-08", "Paid Search – Bing Ads",    "Paid Search",    0.02),
    ("MS-09", "Events & Open Days",        "Events",         0.05),
    ("MS-10", "Other",                     "Other",          0.05),
]

_ACTIVITY_TYPES = ["form_submission", "page_view", "email_open", "email_click", "call_log"]
_ACTIVITY_WEIGHTS = [0.15, 0.45, 0.20, 0.15, 0.05]

_ACTIVITY_DETAILS = {
    "form_submission": [
        "Enquiry form",
        "Open Day registration",
        "Course information request",
        "Apply Now form",
        "Scholarship enquiry",
    ],
    "page_view": [
        "Course page",
        "Fees and funding page",
        "Open Day page",
        "Student outcomes page",
        "About JMC page",
    ],
    "email_open": [
        "Open Day invite",
        "Course guide",
        "Application reminder",
        "Welcome email",
        "Scholarship opportunity",
    ],
    "email_click": [
        "Apply Now CTA",
        "Download course guide",
        "Book a campus tour",
        "View student work",
        "Register for Open Day",
    ],
    "call_log": [
        "Inbound course enquiry",
        "Outbound follow-up",
        "Application support call",
        "Fee and funding query",
    ],
}

# Lifecycle weight for activity distribution — enrolled contacts get more activity
_LIFECYCLE_ACTIVITY_WEIGHT = {"enrolled": 4, "applicant": 2, "lead": 1}


def generate_hubspot() -> dict:
    rng = random.Random(RANDOM_SEED)
    fake = Faker("en_AU")
    fake.seed_instance(RANDOM_SEED)

    marketing_sources = [
        {"marketing_source_id": sid, "source_name": name, "source_category": cat}
        for sid, name, cat, _ in _SOURCES
    ]
    source_ids = [s["marketing_source_id"] for s in marketing_sources]
    source_weights = [w for _, _, _, w in _SOURCES]

    # Lifecycle stage allocation
    num_enrolled = int(D365_STUDENT_COUNT * D365_CONTACT_LINK_RATE)       # 270
    num_applicant = int((HUBSPOT_CONTACT_COUNT - num_enrolled) * 0.27)    # ~197
    num_lead = HUBSPOT_CONTACT_COUNT - num_enrolled - num_applicant
    stages = ["enrolled"] * num_enrolled + ["applicant"] * num_applicant + ["lead"] * num_lead
    rng.shuffle(stages)

    start_date = date(2023, 1, 1)
    end_date = date(2025, 6, 30)
    date_span = (end_date - start_date).days

    # Unique contact IDs (non-sequential)
    contact_id_pool = rng.sample(range(100000, 999999), HUBSPOT_CONTACT_COUNT)

    contacts = []
    for i in range(HUBSPOT_CONTACT_COUNT):
        base_email = fake.email().lower()
        cased_email = apply_email_casing(base_email, rng)
        created_days = rng.randint(0, date_span)
        created = start_date + timedelta(days=created_days)
        modified = created + timedelta(days=rng.randint(0, (end_date - created).days or 1))

        contacts.append({
            "contact_id": f"HS-{contact_id_pool[i]}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": cased_email,
            "_email_base": base_email,          # internal — stripped before JSON output
            "phone": fake.phone_number(),
            "lifecycle_stage": stages[i],
            "marketing_source_id": rng.choices(source_ids, weights=source_weights)[0],
            "created_date": str(created),
            "last_modified_date": str(modified),
        })

    # Activities — weighted toward enrolled/applicant contacts
    activity_weights = [_LIFECYCLE_ACTIVITY_WEIGHT[c["lifecycle_stage"]] for c in contacts]
    activity_contacts = rng.choices(contacts, weights=activity_weights, k=HUBSPOT_ACTIVITY_COUNT)

    activity_id_pool = rng.sample(range(1000000, 9999999), HUBSPOT_ACTIVITY_COUNT)
    activities = []
    for i, contact in enumerate(activity_contacts):
        activity_type = rng.choices(_ACTIVITY_TYPES, weights=_ACTIVITY_WEIGHTS)[0]
        activity_date = start_date + timedelta(days=rng.randint(0, date_span))
        activities.append({
            "activity_id": f"ACT-{activity_id_pool[i]}",
            "contact_id": contact["contact_id"],
            "marketing_source_id": contact["marketing_source_id"],
            "activity_type": activity_type,
            "activity_date": str(activity_date),
            "activity_detail": rng.choice(_ACTIVITY_DETAILS[activity_type]),
        })

    _write_output(marketing_sources, contacts, activities)

    logger.info(
        f"HubSpot: {len(marketing_sources)} sources | {len(contacts)} contacts "
        f"({num_enrolled} enrolled, {num_applicant} applicant, {num_lead} lead) | "
        f"{len(activities)} activities"
    )
    return {"marketing_sources": marketing_sources, "contacts": contacts, "activities": activities}


def _write_output(marketing_sources: list, contacts: list, activities: list) -> None:
    out = os.path.join(OUTPUT_BASE_PATH, "hubspot")
    os.makedirs(out, exist_ok=True)

    with open(os.path.join(out, "marketing_sources.json"), "w", encoding="utf-8") as f:
        json.dump(marketing_sources, f, indent=2, ensure_ascii=False)

    # Strip internal _* keys before writing
    clean_contacts = [{k: v for k, v in c.items() if not k.startswith("_")} for c in contacts]
    with open(os.path.join(out, "contacts.json"), "w", encoding="utf-8") as f:
        json.dump(clean_contacts, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out, "activities.json"), "w", encoding="utf-8") as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)
