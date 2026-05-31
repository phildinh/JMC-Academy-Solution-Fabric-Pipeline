# Data Model — Attributes

Column-level schema for every source entity produced by the data generator. This is the contract for downstream silver and gold work. Generated schemas are definitive — update this file if the generator changes.

All files are written to `output/<source>/` by `python -m data_generator.main`.

---

## HubSpot

### `hubspot/marketing_sources.json`

10 acquisition channels. Each contact and activity references one of these sources.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `marketing_source_id` | string | No | `MS-01` | Primary key. Format: `MS-{nn}`. |
| `source_name` | string | No | `Paid Social – Facebook` | Display name of the acquisition channel. |
| `source_category` | string | No | `Paid Social` | Rolled-up channel category for dashboard grouping. |

**PK:** `marketing_source_id`

**Source categories:** Paid Social, Organic Search, Referral, Email, Paid Search, Events, Other.

---

### `hubspot/contacts.json`

Pre-enrolment leads tracked in HubSpot CRM. Contacts at the `enrolled` stage have a corresponding D365 Student.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `contact_id` | string | No | `HS-528361` | Primary key. Format: `HS-{6-digit random}`. |
| `first_name` | string | No | `Donald` | Given name. |
| `last_name` | string | No | `Garcia` | Family name. |
| `email` | string | No | `Phartman@Example.com` | Contact email. ~30% have non-lowercase casing. |
| `phone` | string | No | `0419-600-133` | Australian phone number. |
| `lifecycle_stage` | string | No | `lead` | Funnel stage. Values: `lead`, `applicant`, `enrolled`. |
| `marketing_source_id` | string | No | `MS-02` | FK → `marketing_sources.marketing_source_id`. |
| `created_date` | string (date) | No | `2023-06-26` | Date contact was created. Range: 2023-01-01 to 2025-06-30. |
| `last_modified_date` | string (date) | No | `2023-08-05` | Date record was last updated. Always ≥ `created_date`. |

**PK:** `contact_id`  
**FK:** `marketing_source_id` → `marketing_sources.marketing_source_id`

**Lifecycle stage distribution:** 27% enrolled, 20% applicant, 53% lead.

**Mess:** ~30% of emails have non-lowercase casing — either all-uppercase (`PHIL@EXAMPLE.COM`) or capitalised-local (`Phil@Example.com`).

**Cross-system note:** Contacts with `lifecycle_stage = 'enrolled'` have a corresponding D365 Student. Their `contact_id` is stored on the D365 Student record as the cross-system key.

---

### `hubspot/activities.json`

CRM interaction events. Weighted toward enrolled and applicant contacts (4×/2× vs lead 1×).

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `activity_id` | string | No | `ACT-8594054` | Primary key. Format: `ACT-{7-digit random}`. |
| `contact_id` | string | No | `HS-928381` | FK → `contacts.contact_id`. |
| `marketing_source_id` | string | No | `MS-05` | FK → `marketing_sources.marketing_source_id`. Inherited from contact. |
| `activity_type` | string | No | `form_submission` | Type of interaction. Values: `form_submission`, `page_view`, `email_open`, `email_click`, `call_log`. |
| `activity_date` | string (date) | No | `2025-04-10` | Date the activity occurred. Range: 2023-01-01 to 2025-06-30. |
| `activity_detail` | string | No | `Enquiry form` | Short description of the specific activity. |

**PK:** `activity_id`  
**FK:** `contact_id` → `contacts.contact_id`; `marketing_source_id` → `marketing_sources.marketing_source_id`

**Activity type distribution:** ~45% page_view, ~20% email_open, ~15% email_click, ~15% form_submission, ~5% call_log.

---

## Dynamics 365

### `dynamics365/courses.csv`

The 20-course JMC Academy catalogue. `course_code` is the cross-system FK consumed by Paradigm units.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `course_id` | string | No | `COURSE-01` | Primary key. Format: `COURSE-{nn}`. |
| `course_code` | string | No | `BACH-MPROD` | Short code. Cross-system FK used by Paradigm units. |
| `course_name` | string | No | `Bachelor of Music Production` | Full course title. Real JMC Academy course names. |
| `course_level` | string | No | `Bachelor` | Academic level. Values: `Certificate IV`, `Diploma`, `Bachelor`, `Graduate Diploma`, `Master`. |
| `duration_terms` | integer | No | `6` | Standard duration in terms. Certificate IV=2, Diploma=4, Bachelor=6, Postgrad=4. |

**PK:** `course_id`  
**Alternate key:** `course_code` (cross-system FK in Paradigm)

---

### `dynamics365/intakes.csv`

Six study periods spanning 2023–2025, two per year. `intake_code` is the cross-system FK consumed by Paradigm results.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `intake_id` | string | No | `INT-01` | Primary key. Format: `INT-{nn}`. |
| `intake_code` | string | No | `2023-T1` | Human-readable code. Format: `{YYYY}-T{n}`. Cross-system FK in Paradigm results. |
| `start_date` | string (date) | No | `2023-02-06` | First day of intake. |
| `end_date` | string (date) | No | `2023-06-30` | Last day of intake. |
| `academic_year` | integer | No | `2023` | Calendar year of the intake. Values: 2023, 2024, 2025. |
| `term` | string | No | `T1` | Term within the year. Values: `T1`, `T2`. |

**PK:** `intake_id`  
**Alternate key:** `intake_code` (cross-system FK in Paradigm)

**Intakes:** 2023-T1, 2023-T2, 2024-T1, 2024-T2, 2025-T1, 2025-T2.

---

### `dynamics365/students.csv`

Official student enrolment records. 90% of students have a HubSpot origin; 10% are walk-ins with no CRM record.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `student_number` | string | No | `JMC2024-0029` | Primary key. Format: `JMC{YYYY}-{seq:04d}`. |
| `contact_id` | string | **Yes** | `HS-547494` | FK → HubSpot `contacts.contact_id`. NULL for ~10% of students (walk-ins). |
| `first_name` | string | No | `Daniel` | Given name. Matches HubSpot contact for linked students. |
| `last_name` | string | No | `Moyer` | Family name. Matches HubSpot contact for linked students. |
| `email` | string | No | `lrodriguez@example.net` | Student email. ~30% non-lowercase casing. Base matches HubSpot for linked students — casing may differ. |
| `phone` | string | No | `+61 8 3651 5597` | Australian phone number. |
| `date_of_birth` | string (date) | No | `2007-02-11` | Date of birth. Age range: 17–40. |
| `address_suburb` | string | No | `Alisonton` | Suburb of residence. |
| `address_state` | string | No | `QLD` | Australian state/territory. Values: NSW, VIC, QLD, SA, WA, ACT, TAS, NT. |
| `lifecycle_status` | string | No | `enrolled` | Current student status. Values: `applied`, `enrolled`, `graduated`, `withdrew`. |
| `enrolment_date` | string (date) | No | `2025-04-14` | Date the student first enrolled. Range: 2023-01-01 to 2025-06-30. |

**PK:** `student_number`  
**FK:** `contact_id` → `hubspot/contacts.contact_id` (nullable — walk-ins have no HubSpot record)

**Lifecycle status distribution:** ~53% enrolled, ~22% applied, ~15% graduated, ~10% withdrew.

**Mess:** `contact_id` is NULL for ~10% of students (walk-ins). ~30% of emails have non-lowercase casing.

**Cross-system note:** Silver joins D365 ↔ HubSpot via `contact_id` (direct). Silver joins D365 ↔ Paradigm via `LOWER(TRIM(email))`.

---

### `dynamics365/enrolments.csv`

Course enrolment records. One student may have multiple enrolments across different courses and intakes.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `enrolment_id` | string | No | `ENR-4212252` | Primary key. Format: `ENR-{7-digit random}`. |
| `student_number` | string | No | `JMC2023-0054` | FK → `students.student_number`. |
| `course_id` | string | No | `COURSE-17` | FK → `courses.course_id`. |
| `intake_id` | string | No | `INT-05` | FK → `intakes.intake_id`. |
| `enrolment_date` | string (date) | No | `2025-01-27` | Date of enrolment. Within 7 days before / 14 days after intake start. |
| `status` | string | No | `active` | Enrolment status. Values: `active`, `completed`, `withdrawn`. |
| `final_grade` | integer | **Yes** | `72` | Numeric final grade 0–100. Only populated when `status = 'completed'`; empty string in CSV otherwise. |

**PK:** `enrolment_id`  
**FK:** `student_number` → `students.student_number`; `course_id` → `courses.course_id`; `intake_id` → `intakes.intake_id`

**Status distribution:** ~55% active, ~37% completed, ~9% withdrawn.

**Mess:** `final_grade` is an empty string `""` in CSV for non-completed rows (not Python `None`). Silver must handle this when casting to integer.

---

## Paradigm

### `paradigm/students.csv`

Students with results recorded in the academic management system. A subset (~83%) of D365 students.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `student_code` | string | No | `P265346` | Primary key. Format: `P{6-digit random}`. Unique within Paradigm. |
| `first_name` | string | No | `Zachary` | Given name. Matches the corresponding D365 student. |
| `last_name` | string | No | `Fisher` | Family name. Matches the corresponding D365 student. |
| `email` | string | No | `Bbarrett@Example.net` | Student email. ~30% non-lowercase casing. Base email matches D365 student — casing may differ. |

**PK:** `student_code`

**Coverage:** ~83% of D365 students (250 of 300) appear in Paradigm. The remaining ~17% are enrolled but have no results recorded yet.

**Mess:** ~30% of emails have non-lowercase casing. Paradigm does not store D365's `student_number` or HubSpot's `contact_id` — silver resolves identity via `LOWER(TRIM(email))`.

---

### `paradigm/units.csv`

Academic units (subjects). 5 units per course × 20 courses = 100 units total. References D365 courses via `course_code`.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `unit_id` | string | No | `UNIT-0001` | Primary key. Format: `UNIT-{seq:04d}`. |
| `unit_code` | string | No | `MUS101` | Short code. Derived from course code suffix + level number (101–202). |
| `unit_name` | string | No | `Certificate IV in Music Industry - Foundations` | Full name. Pattern: `{course_name} - {topic}`. |
| `course_code` | string | No | `CERT4-MUS` | FK → `dynamics365/courses.course_code`. Cross-system link. |

**PK:** `unit_id`  
**FK:** `course_code` → `dynamics365/courses.course_code`

**Unit topics (in order per course):** Foundations, Core Skills, Applied Practice, Advanced Techniques, Industry Project.

---

### `paradigm/results.csv`

Student assessment results. One row per `(student_code, unit_id)` — no duplicate attempts.

| Column | Type | Nullable | Example | Description |
|---|---|---|---|---|
| `result_id` | string | No | `RES-7447430` | Primary key. Format: `RES-{7-digit random}`. |
| `student_code` | string | No | `P265346` | FK → `students.student_code`. |
| `unit_id` | string | No | `UNIT-0046` | FK → `units.unit_id`. |
| `intake_code` | string | No | `2024-T2` | FK → `dynamics365/intakes.intake_code`. Cross-system FK via string match. |
| `mark` | integer | No | `38` | Numeric mark 0–100. Normally distributed around 70 (σ=15), clamped to [0, 100]. |
| `grade` | string | No | `F` | Grade band derived from mark. Values: `HD` (≥85), `D` (≥75), `C` (≥65), `P` (≥50), `F` (<50). |
| `result_date` | string (date) | No | `2024-11-07` | Date result was recorded. Falls in the final 20% of the intake period. |

**PK:** `result_id`  
**Unique constraint:** `(student_code, unit_id)` — each student attempts each unit at most once.  
**FK:** `student_code` → `students.student_code`; `unit_id` → `units.unit_id`; `intake_code` → `dynamics365/intakes.intake_code`

**Grade distribution:** HD ~18%, D ~19%, C ~27%, P ~28%, F ~9%.

---

## Identity Resolution Summary

How silver resolves the same real person across three systems that share no common ID.

| Link | Key | Silver join | Notes |
|---|---|---|---|
| HubSpot Contact ↔ D365 Student | `d365.contact_id = hubspot.contact_id` | Direct equality join | ~10% of D365 students have NULL `contact_id` — use LEFT JOIN from D365 |
| D365 Student ↔ Paradigm Student | `LOWER(TRIM(d365.email)) = LOWER(TRIM(paradigm.email))` | Case-insensitive email match | ~17% of D365 students have no Paradigm record |
| D365 Course ↔ Paradigm Unit | `d365.course_code = paradigm.course_code` | Direct string match | Stable codes — no fuzzy matching needed |
| D365 Intake ↔ Paradigm Result | `d365.intake_code = paradigm.intake_code` | Direct string match | Stable codes — no fuzzy matching needed |
