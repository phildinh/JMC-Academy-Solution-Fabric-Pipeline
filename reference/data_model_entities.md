# Data Model — Entities

The conceptual entity model and relationships across the three in-scope source systems. This document defines **what entities exist and how they relate**. Source landscape is in `data_model_sources.md`. Column-level detail is in `data_model_attributes.md` (built iteratively after the data generator).

---

## High-Level Entity Map

```
┌─ HubSpot ───────────────────┐  ┌─ D365 ───────────────────────┐  ┌─ Paradigm ──────────────┐
│                              │  │                               │  │                          │
│  Marketing_Source            │  │   Intake          Course      │  │   Paradigm_Student      │
│        │ 1                   │  │      │ 1            │ 1       │  │          │ 1            │
│        ▼ *                   │  │      ▼ *            ▼ *       │  │          ▼ *            │
│     Activity *──1 Contact ───┼──┼──▶ Enrolment *──────────┘     │  │       Result *──1 Unit  │
│                              │  │                                │  │                          │
│                              │  │            Student ◄───1:0..1──┼──┼─▶ Paradigm_Student      │
└──────────────────────────────┘  └───────────────────────────────┘  └──────────────────────────┘
```

(All cross-source links are drawn as single-style arrows for simplicity. In production, cross-source linkages are resolved by the silver layer — see `data_model_sources.md` for the resolution strategy.)

---

## Entities By Source

### HubSpot (3 entities)

| Entity | Purpose | Type |
|---|---|---|
| **Marketing_Source** | Channel that brought the lead in (paid social, organic, email, referral) | Dimension |
| **Contact** | The prospect / lead | Master entity |
| **Activity** | Logged interactions (form fills, page views, email opens) | Event / fact |

### Dynamics 365 (4 entities)

| Entity | Purpose | Type |
|---|---|---|
| **Student** | Official student record | Master entity |
| **Course** | Course catalogue (e.g. Bachelor of Music Production) | Dimension |
| **Intake** | Term / semester (e.g. 2025-T1) | Dimension |
| **Enrolment** | Student joining a course at an intake | Event / fact |

### Paradigm (3 entities)

| Entity | Purpose | Type |
|---|---|---|
| **Paradigm_Student** | Student identity in Paradigm (separate from D365) | Master entity |
| **Unit** | A subject within a course | Dimension |
| **Result** | A student's outcome in a unit | Event / fact |

**Total: 10 entities across 3 sources.**

---

## Relationships

### Within HubSpot

| Relationship | Cardinality | Notes |
|---|---|---|
| Marketing_Source → Activity | 1 : M | One source generates many activities |
| Contact → Activity | 1 : M | One contact has many activities over time |

### Within Dynamics 365

| Relationship | Cardinality | Notes |
|---|---|---|
| Student → Enrolment | 1 : M | A student enrols in many courses/intakes over time |
| Course → Enrolment | 1 : M | A course has many enrolments |
| Intake → Enrolment | 1 : M | An intake contains many enrolments |

### Within Paradigm

| Relationship | Cardinality | Notes |
|---|---|---|
| Paradigm_Student → Result | 1 : M | A student has many results across units |
| Unit → Result | 1 : M | A unit has many student results |
| Course → Unit | 1 : M | A course contains many units (FK on Unit) |

### Cross-Source (Resolved In Silver)

| Relationship | Cardinality | Resolution mechanism |
|---|---|---|
| Contact ↔ Student | 1 : 0..1 | Deterministic: `Student.contact_id` stored by the HubSpot ↔ D365 integration |
| Student ↔ Paradigm_Student | 1 : 0..1 | Email match (case-insensitive, normalised) |

---

## Why Every Entity Earns Its Place

Each entity is required by at least one of the business questions in `business_questions.md`:

| Entity | Q1 (Funnel) | Q2 (Quality) |
|---|---|---|
| Marketing_Source | ✓ | ✓ |
| Contact | ✓ | ✓ |
| Activity | ✓ | ✓ |
| Student | ✓ | ✓ |
| Enrolment | ✓ | ✓ |
| Course | ✓ | ✓ |
| Intake | ✓ | ✓ |
| Paradigm_Student | | ✓ |
| Unit | | ✓ |
| Result | | ✓ |

No entity is decorative. If a future requirement adds an entity, it must serve a documented question.

---

## Modelling Decisions Worth Noting

### Why Activity is a fact, not a bridge between Contact and Marketing_Source

Activity is an **event** (a contact did a thing at a point in time), not a pure link. It has its own attributes (timestamp, type, content) and its own identity. The Contact ↔ Marketing_Source relationship is mediated through Activity events rather than a separate bridge table.

### Why Enrolment is a fact, not a bridge between Student and Course

Enrolment records an event (a student joined a course in a specific intake). It has its own attributes (enrolment date, status, final grade) and its own identity. Promoting it to a fact instead of a bridge avoids the many-to-many anti-pattern in Power BI.

### Why Contact ↔ Student is 1:0..1

In a mature HubSpot ↔ D365 integration, the HubSpot `contact_id` is written to the D365 Student record when a Contact progresses to application stage. One Contact maps to at most one Student. Some Students (walk-ins, internal referrals, integration gaps) may have no corresponding Contact.

### Why Paradigm has its own Student entity

Paradigm operates as an independent system with its own student identity. In bronze, `paradigm_student` is preserved as-is from the source. Silver resolves it to the same logical person as `d365_student` via email matching, producing a single `silver_student` master entity.

### Why Unit is kept simple (no Assessment)

For the demo, Result is recorded at unit level (one final grade per student per unit). Assessment-level granularity (individual exam / assignment results) was scoped out — Q2 only requires unit-level outcomes. Adding Assessment in production would be a straightforward extension of the model.

### Why no SCD Type 2

For the demo, all entities are stored as current-state snapshots. Event history is naturally captured by event tables (Activity, Enrolment, Result) — each row has its own timestamp. Attribute history on master entities (Student status changes, Contact marketing source re-attribution) would be implemented as SCD Type 2 in production but is out of scope for this demo, which has only one data snapshot.

---

## Layer-Specific Modelling Approach

The entity model above describes the conceptual state. Each medallion layer applies a different modelling discipline:

| Layer | Approach |
|---|---|
| **Bronze** | Mirrors source structure faithfully. One bronze table per source entity. No transformation. |
| **Silver** | 3NF, conformed entities. Cross-source identities resolved (single `silver_student`). Cleaned, typed, deduplicated. |
| **Gold** | Star schema (deliberately denormalised). Facts and dimensions sized for analytics performance. Power BI semantic model built on top via Direct Lake. |

Bronze and silver table names follow the pattern in `data_model_sources.md`. Gold dimension and fact names will be defined during the build and recorded in `data_model_attributes.md`.
