# Data Model — Sources

The source-system landscape that feeds the JMC student data consolidation pipeline. This document describes **where data comes from** before any modelling work. Entity structure within each source is in `data_model_entities.md`. Column-level detail is in `data_model_attributes.md`.

---

## In-Scope Sources

Three operational systems feed the demo pipeline. Each owns a distinct slice of the student lifecycle.

```
┌──────────────────┐
│    HubSpot       │     Pre-enrolment leads, marketing source, contact activity
└─────────┬────────┘
          │
          │ data
          ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   Dynamics 365   │ ──data─▶│    MS Fabric     │ ──data─▶│     Power BI     │
└──────────────────┘         │   (Lakehouse)    │         │  (Direct Lake)   │
          ▲                  └──────────────────┘         └──────────────────┘
          │ data
          │
┌─────────┴────────┐
│    Paradigm      │     Academic results, grades
└──────────────────┘
```

| Source | Owns | Update rhythm | Demo format | Ingestion method |
|---|---|---|---|---|
| **HubSpot** | Pre-enrolment leads, marketing source, contact details, funnel activities | Continuous (CRM activity) | JSON | Notebook (API-style) |
| **Dynamics 365** | Official student record, enrolments, courses, intakes | Daily (enrolment events) | CSV | Copy Job |
| **Paradigm** | Academic results, unit-level grades | Batched (end of term) | CSV | Copy Job |

### Why Three Sources

Each source is necessary to answer the business questions defined in `business_questions.md`:

- **Q1 (lead → enrolment funnel)** requires HubSpot + D365
- **Q2 (marketing source × academic success)** requires HubSpot + D365 + Paradigm

Cutting any of the three would make one of the business questions unanswerable.

---

## Out of Scope (For Honesty)

Sources that would exist in a real JMC data platform but are deliberately not in this demo. Documented to show awareness without overpromising.

| Source | What it would contribute | Why out of scope |
|---|---|---|
| **Canvas LMS** | Learning engagement (logins, submissions, time on page) | Cut to focus on JD's headline customer-journey requirement. Would enable Q3 (engagement-based early warning) — see `business_questions.md` Future Enhancement section |
| **TAC (Tertiary Admissions Centre)** | Government-administered application data, ATAR scores, preference rankings | External regulatory source, integration would require formal data-sharing arrangement. Not core to the consolidation pattern |
| **Internal data** | Spreadsheets, manually-maintained tracking files, ad-hoc exports | Common in real institutions but not relevant to demonstrating the medallion pattern |

These sources are visible in the source-landscape diagram but greyed out / annotated as future scope.

---

## The Identity Resolution Problem

Each source has its own student identifier. Email is the only stitchable key across all three — and even that is unreliable in simulated data (typos, case differences, change over time).

```
HubSpot      contact_id          HS-xxxxx          (e.g. HS-789123)
Dynamics 365 student_number      JMC<year>-xxxx    (e.g. JMC2024-042)
Paradigm     student_code        Pxxxxxx           (e.g. P004207)
```

### Cross-Source Linking Strategy

| Link | Mechanism | Where resolved |
|---|---|---|
| HubSpot Contact ↔ D365 Student | Deterministic — D365 stores `contact_id` at integration time | Bronze data preserves the link; silver consumes it directly |
| D365 Student ↔ Paradigm Student | Email match (case-insensitive, normalised) | Silver layer with fallback handling |
| D365 Course ↔ Paradigm Unit | Course code match | Silver layer |

The silver layer's primary job is producing a single `silver_student` master entity that consolidates all three source identities into one row per real person.

### Realistic Mess (Baked Into The Generator)

To make silver's work visible, the data generator produces realistic mess:

- ~5–10% of D365 Students have NULL `contact_id` (walk-in students, integration failures)
- Email casing inconsistencies (`Phil@gmail.com` vs `phil@gmail.com`)
- Email typos in 2–3% of records (e.g. `gmaill.com`)
- Trailing whitespace on names and emails
- ~10–15% of D365 Students have no Paradigm record yet (enrolled but haven't sat assessments)
- Some HubSpot Contacts never convert to D365 Students (unconverted leads)

---

## Source-to-Layer Mapping

| Source | Bronze | Silver | Gold |
|---|---|---|---|
| HubSpot | `bronze_hubspot_contact`, `bronze_hubspot_activity`, `bronze_hubspot_marketing_source` | Conformed into `silver_student`, `silver_lead_activity` | `dim_student`, `dim_marketing_source`, `fact_lead` |
| Dynamics 365 | `bronze_d365_student`, `bronze_d365_enrolment`, `bronze_d365_course`, `bronze_d365_intake` | `silver_student`, `silver_enrolment`, `silver_course` | `dim_student`, `dim_course`, `dim_intake`, `fact_enrolment` |
| Paradigm | `bronze_paradigm_student`, `bronze_paradigm_result`, `bronze_paradigm_unit` | `silver_result`, `silver_unit` | `fact_result` |

Exact silver and gold table names will be confirmed during build and updated in `data_model_attributes.md`.
