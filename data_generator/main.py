import random

from data_generator.generate_dynamics365 import generate_dynamics365
from data_generator.generate_hubspot import generate_hubspot
from data_generator.generate_paradigm import generate_paradigm
from data_generator.utils.config import RANDOM_SEED
from data_generator.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    random.seed(RANDOM_SEED)
    logger.info("Starting data generation (seed=%d)", RANDOM_SEED)

    hs = generate_hubspot()
    d365 = generate_dynamics365(hs_contacts=hs["contacts"])
    paradigm = generate_paradigm(
        d365_students=d365["students"],
        d365_courses=d365["courses"],
    )

    _print_summary(hs, d365, paradigm)
    logger.info("Done.")


def _print_summary(hs: dict, d365: dict, paradigm: dict) -> None:
    contacts = hs["contacts"]
    students = d365["students"]
    p_students = paradigm["students"]

    # --- Row counts ---
    print("\n" + "=" * 60)
    print("OUTPUT FILE SUMMARY")
    print("=" * 60)
    print(f"  hubspot/marketing_sources.json  {len(hs['marketing_sources']):>6} rows")
    print(f"  hubspot/contacts.json           {len(contacts):>6} rows")
    print(f"  hubspot/activities.json         {len(hs['activities']):>6} rows")
    print(f"  dynamics365/courses.csv         {len(d365['courses']):>6} rows")
    print(f"  dynamics365/intakes.csv         {len(d365['intakes']):>6} rows")
    print(f"  dynamics365/students.csv        {len(students):>6} rows")
    print(f"  dynamics365/enrolments.csv      {len(d365['enrolments']):>6} rows")
    print(f"  paradigm/students.csv           {len(p_students):>6} rows")
    print(f"  paradigm/units.csv              {len(paradigm['units']):>6} rows")
    print(f"  paradigm/results.csv            {len(paradigm['results']):>6} rows")

    # --- Mess pattern 1: NULL contact_id ---
    null_contact = sum(1 for s in students if s["contact_id"] is None)
    null_pct = null_contact / len(students) * 100
    print("\n" + "-" * 60)
    print("MESS PATTERN VERIFICATION")
    print("-" * 60)
    print(f"  1. NULL contact_id (D365 walk-ins)")
    print(f"     {null_contact} of {len(students)} students = {null_pct:.1f}%  (target ~10%)")

    # --- Mess pattern 2: Email casing ---
    def is_non_lowercase(email: str) -> bool:
        return email != email.lower()

    hs_cased = sum(1 for c in contacts if is_non_lowercase(c["email"]))
    d365_cased = sum(1 for s in students if is_non_lowercase(s["email"]))
    p_cased = sum(1 for s in p_students if is_non_lowercase(s["email"]))
    hs_pct = hs_cased / len(contacts) * 100
    d365_pct = d365_cased / len(students) * 100
    p_pct = p_cased / len(p_students) * 100
    print(f"\n  2. Non-lowercase email casing  (target ~30% per system)")
    print(f"     HubSpot contacts:    {hs_cased:>4} of {len(contacts)} = {hs_pct:.1f}%")
    print(f"     D365 students:       {d365_cased:>4} of {len(students)} = {d365_pct:.1f}%")
    print(f"     Paradigm students:   {p_cased:>4} of {len(p_students)} = {p_pct:.1f}%")

    # --- Mess pattern 3: Conversion rate ---
    enrolled_contacts = sum(1 for c in contacts if c["lifecycle_stage"] == "enrolled")
    linked_students = sum(1 for s in students if s["contact_id"] is not None)
    conv_pct = linked_students / len(contacts) * 100
    print(f"\n  3. Lead-to-student conversion rate")
    print(f"     {linked_students} students with contact_id / {len(contacts)} HubSpot contacts = {conv_pct:.1f}%")
    print(f"     ({enrolled_contacts} contacts flagged 'enrolled' in HubSpot)")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
