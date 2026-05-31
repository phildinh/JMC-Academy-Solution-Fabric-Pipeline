# Data Model — Attributes

Column-level schema for every source entity produced by the data generator. This is the contract for downstream silver and gold work. Generated schemas are definitive — update this file if the generator changes.

All files are written to `output/<source>/` by `python -m data_generator.main`.

---

## HubSpot

### `hubspot/marketing_sources.json`

| Column | Type | Example | Description |
|---|---|---|---|
| `marketing_source_id` | string | `MS-01` | Primary key. Format: `MS-{nn}`. 10 sources total. |
| `source_name` | string | `Paid Social – Facebook` | Display name of the acquisition channel. |
| `source_category` | string | `Paid Social` | Rolled-up channel category for dashboard grouping. |

**Source categories:** Paid Social, Organic Search, Referral, Email, Paid Search, Events, Other.

---

### `hubspot/contacts.json`

| Column | Type | Example | Description |
|---|---|---|---|
| `contact_id` | string | `HS-528361` | Primary key. Format: `HS-{6-digit random}`. Unique. |
| `first_name` | string | `Donald` | Given name. |
| `last_name` | string | `Garcia` | Family name. |
| `email` | string | `Phartman@Example.com` | Contact email. ~30% have uppercase or mixed-case casing. |
| `phone` | string | `0419-600-133` | Australian phone number. |
| `lifecycle_stage` | string | `enrolled` | Funnel stage. Values: `lead`, `applicant`, `enrolled`. |
| `marketing_source_id` | string | `MS-02` | FK → `marketing_sources.marketing_source_id`. |
| `created_date` | string (date) | `2023-06-26` | Date contact was created in HubSpot. Range: 2023-01-01 to 2025-06-30. |
| `last_modified_date` | string (date) | `2023-08-05` | Date contact record was last updated. Always ≥ `created_date`. |

**Lifecycle stage distribution (approximate):** 27% enrolled, 20% applicant, 53% lead.

**Cross-system note:** Contacts with `lifecycle_stage = 'enrolled'` have a corresponding D365 Student. Their `contact_id` is stored on the D365 Student record as the cross-system key.

---

### `hubspot/activities.json`

| Column | Type | Example | Description |
|---|---|---|---|
| `activity_id` | string | `ACT-8594054` | Primary key. Format: `ACT-{7-digit random}`. |
| `contact_id` | string | `HS-928381` | FK → `contacts.contact_id`. |
| `marketing_source_id` | string | `MS-05` | FK → `marketing_sources.marketing_source_id`. Inherited from contact. |
| `activity_type` | string | `form_submission` | Type of interaction. Values: `form_submission`, `page_view`, `email_open`, `email_click`, `call_log`. |
| `activity_date` | string (date) | `2025-04-10` | Date the activity occurred. Range: 2023-01-01 to 2025-06-30. |
| `activity_detail` | string | `Enquiry form` | Short description of the specific activity. |

**Activity type distribution (approximate):** 45% page_view, 20% email_open, 15% form_submission, 15% email_click, 5% call_log.

---

## Dynamics 365

### `dynamics365/courses.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `course_id` | string | `COURSE-01` | Primary key. Format: `COURSE-{nn}`. 20 courses. |
| `course_code` | string | `BACH-MPROD` | Short course code used as cross-system FK (e.g. Paradigm Units reference this). |
| `course_name` | string | `Bachelor of Music Production` | Full course title. Real JMC Academy course names. |
| `course_level` | string | `Bachelor` | Academic level. Values: `Certificate IV`, `Diploma`, `Bachelor`, `Graduate Diploma`, `Master`. |
| `duration_terms` | integer | `6` | Standard duration in terms. Certificate IV = 2, Diploma = 4, Bachelor = 6, Postgrad = 4. |

---

### `dynamics365/intakes.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `intake_id` | string | `INT-01` | Primary key. Format: `INT-{nn}`. 6 intakes. |
| `intake_code` | string | `2023-T1` | Human-readable intake identifier. Format: `{YYYY}-T{n}`. Used as cross-system FK in Paradigm Results. |
| `start_date` | string (date) | `2023-02-06` | First day of intake. |
| `end_date` | string (date) | `2023-06-30` | Last day of intake. |
| `academic_year` | integer | `2023` | Calendar year of the intake. Values: 2023, 2024, 2025. |
| `term` | string | `T1` | Term within the academic year. Values: `T1`, `T2`. |

**Intakes:** 2023-T1, 2023-T2, 2024-T1, 2024-T2, 2025-T1, 2025-T2.

---

### `dynamics365/students.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `student_number` | string | `JMC2024-0029` | Primary key. Format: `JMC{YYYY}-{seq:04d}`. Unique across all students. |
| `contact_id` | string / null | `HS-547494` | FK → HubSpot `contacts.contact_id`. NULL for ~10% of students (walk-ins). |
| `first_name` | string | `Daniel` | Given name. Matches HubSpot contact for linked students. |
| `last_name` | string | `Moyer` | Family name. Matches HubSpot contact for linked students. |
| `email` | string | `lrodriguez@example.net` | Student email. ~30% have uppercase or mixed-case casing. Base email matches HubSpot contact's email for linked students — casing may differ. |
| `phone` | string | `+61 8 3651 5597` | Australian phone number. |
| `date_of_birth` | string (date) | `2007-02-11` | Date of birth. Age range: 17–40 at time of enrolment. |
| `address_suburb` | string | `Alisonton` | Suburb of residence. |
| `address_state` | string | `QLD` | Australian state/territory. |
| `lifecycle_status` | string | `enrolled` | Current student status. Values: `applied`, `enrolled`, `graduated`, `withdrew`. |
| `enrolment_date` | string (date) | `2025-04-14` | Date the student first enrolled. Range: 2023-01-01 to 2025-06-30. |

**Lifecycle status distribution (approximate):** 55% enrolled, 20% applied, 15% graduated, 10% withdrew.

**Cross-system note:** The `contact_id` field is the deterministic cross-system key between HubSpot and D365. Silver consumes this directly without needing fuzzy matching.

---

### `dynamics365/enrolments.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `enrolment_id` | string | `ENR-4212252` | Primary key. Format: `ENR-{7-digit random}`. |
| `student_number` | string | `JMC2023-0054` | FK → `students.student_number`. |
| `course_id` | string | `COURSE-17` | FK → `courses.course_id`. |
| `intake_id` | string | `INT-05` | FK → `intakes.intake_id`. |
| `enrolment_date` | string (date) | `2025-01-27` | Date of enrolment. Within 7 days before / 14 days after intake start. |
| `status` | string | `active` | Enrolment status. Values: `active`, `completed`, `withdrawn`. |
| `final_grade` | integer / null | `72` | Numeric final grade 0–100. Only populated when `status = 'completed'`. NULL otherwise. |

**Status distribution (approximate):** 55% active, 35% completed, 10% withdrawn.

---

## Paradigm

### `paradigm/students.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `student_code` | string | `P265346` | Primary key. Format: `P{6-digit random}`. Unique within Paradigm. |
| `first_name` | string | `Zachary` | Given name. Matches corresponding D365 student. |
| `last_name` | string | `Fisher` | Family name. Matches corresponding D365 student. |
| `email` | string | `Bbarrett@Example.net` | Student email. ~30% have uppercase or mixed-case casing. Base email matches D365 student — casing may differ. |

**Coverage:** ~83% of D365 students (250 of 300) appear in Paradigm. The remaining ~17% are enrolled but have not yet had results recorded.

**Cross-system note:** Paradigm does not store D365's `student_number` or HubSpot's `contact_id`. Silver resolves D365 ↔ Paradigm identity via case-insensitive email match.

---

### `paradigm/units.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `unit_id` | string | `UNIT-0001` | Primary key. Format: `UNIT-{seq:04d}`. 100 units total (5 per course × 20 courses). |
| `unit_code` | string | `MUS101` | Short unit code. Derived from course code suffix + level number (101–202). |
| `unit_name` | string | `Certificate IV in Music Industry - Foundations` | Full unit name. Pattern: `{course_name} - {topic}`. |
| `course_code` | string | `CERT4-MUS` | FK → `dynamics365/courses.course_code`. Cross-system link between Paradigm units and D365 courses. |

**Unit topics (in order):** Foundations, Core Skills, Applied Practice, Advanced Techniques, Industry Project.

---

### `paradigm/results.csv`

| Column | Type | Example | Description |
|---|---|---|---|
| `result_id` | string | `RES-7447430` | Primary key. Format: `RES-{7-digit random}`. |
| `student_code` | string | `P265346` | FK → `students.student_code`. |
| `unit_id` | string | `UNIT-0046` | FK → `units.unit_id`. |
| `intake_code` | string | `2024-T2` | FK → `dynamics365/intakes.intake_code`. Cross-system FK via intake code string. |
| `mark` | integer | `38` | Numeric mark 0–100. Normally distributed around 70 (σ=15), clamped to [0, 100]. |
| `grade` | string | `F` | Grade band. Derived from mark: HD (≥85), D (≥75), C (≥65), P (≥50), F (<50). |
| `result_date` | string (date) | `2024-11-07` | Date result was recorded. Falls in the final 20% of the intake period. |

**Grade distribution (approximate):** HD ~16%, D ~23%, C ~26%, P ~25%, F ~9%.

**Uniqueness constraint:** Each (student_code, unit_id) combination appears at most once.

---

## Identity Resolution Summary

| Link | Mechanism | Silver action |
|---|---|---|
| HubSpot Contact ↔ D365 Student | `d365.students.contact_id = hubspot.contacts.contact_id` (deterministic) | Direct join. ~10% of students have NULL contact_id (walk-ins). |
| D365 Student ↔ Paradigm Student | `LOWER(TRIM(d365.students.email)) = LOWER(TRIM(paradigm.students.email))` | Case-insensitive email match. ~17% of D365 students have no Paradigm record. |
| D365 Course ↔ Paradigm Unit | `d365.courses.course_code = paradigm.units.course_code` | Direct string match. |
| D365 Intake ↔ Paradigm Result | `d365.intakes.intake_code = paradigm.results.intake_code` | Direct string match. |
