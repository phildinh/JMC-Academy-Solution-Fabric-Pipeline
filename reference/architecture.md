# Architecture

End-to-end architecture for the JMC student data consolidation demo on Microsoft Fabric.

---

## 1. High-Level View

```
┌──────────────────┐     ┌────────────────────────────────────────────┐     ┌──────────────┐
│   LOCAL LAPTOP   │     │            MICROSOFT FABRIC                │     │   POWER BI   │
│                  │     │              (My Workspace)                │     │              │
│  Python          │     │                                            │     │  Direct Lake │
│  data_generator  │     │  OneLake (Lakehouse)                       │     │  semantic    │
│                  │     │  ┌────────────┬──────────────────────────┐ │     │  model       │
│  output/         │ ──▶ │  │  Files/    │   Tables/                │ │ ──▶ │              │
│  ├ hubspot/      │     │  │  raw/      │   ├ bronze_*  Delta      │ │     │  Report      │
│  ├ dynamics365/  │     │  │  ├─hubspot │   ├ silver_*  Delta      │ │     │  (answers    │
│  ├ paradigm/     │     │  │  ├─d365    │   └ gold_*    Delta      │ │     │   business   │
│  └ canvas/       │     │  │  ├─paradigm│                          │ │     │   questions) │
│                  │     │  │  └─canvas  │                          │ │     │              │
└──────────────────┘     │  └────────────┴──────────────────────────┘ │     └──────────────┘
        │                │                                            │
        │ manual upload  │  Data Pipeline (orchestration)             │
        │ (OneLake       │  └─ Copy Jobs + Notebooks + Outlook email  │
        │  Explorer)     │                                            │
        └────────────────┘                                            │
                         └────────────────────────────────────────────┘
```

---

## 2. Why Medallion Architecture

Three layers, each with a single responsibility. The discipline pays off when something breaks — you know exactly which layer to look in.

| Layer | Purpose | What lives here | What does NOT live here |
|---|---|---|---|
| **Bronze** | Faithful copy of source data | Raw rows, all columns, all mess | Cleaning, joins, business logic |
| **Silver** | Cleaned, conformed, deduplicated | Typed columns, standard IDs, one row per real entity | Aggregations, business KPIs |
| **Gold** | Business-ready, modelled for analytics | Star schema, KPIs, joined facts | Raw source columns, technical fields |

**The rule:** bronze can be rebuilt from sources, silver can be rebuilt from bronze, gold can be rebuilt from silver. No layer skips. This is what makes the architecture debuggable and replayable.

---

## 3. The Four Source Systems

| Source | Owns | Update rhythm | Simulated format | Ingestion method |
|---|---|---|---|---|
| **HubSpot** | Pre-enrolment leads, marketing source, contact details | Continuous | JSON | Notebook (API-style) |
| **Dynamics 365** | Official enrolment, course, intake, student status | Daily | CSV | Copy Job |
| **Paradigm** | Academic results, grades, assessments | Batched (end of term) | CSV | Copy Job |
| **Canvas** | LMS engagement, logins, submissions | Daily | CSV | Notebook (API-style) |

### The Identity Problem

Each system has its own student identifier. Email is the only stitchable key across all four — and even that is unreliable in the simulated data (typos, case differences). Resolving this is the core job of the silver layer.

The resolution strategy is documented in `reference/data_model_attributes.md` — Identity Resolution Summary. Short version: D365 is the spine, HubSpot joins via `contact_id` (direct FK), Paradigm joins via `LOWER(TRIM(email))` match (no shared ID exists).

---

## 4. Ingestion Strategy — Hybrid By Design

Real production data ingestion is never one-size-fits-all. Each source dictates its own best path.

**Copy Job — for sources with native connectors or file-based delivery**
- **Dynamics 365** → Dataverse connector in production. Demo uses Copy Job from staged CSV in OneLake Files.
- **Paradigm** → Batch file exports from SIS. Copy Job is the natural fit.

**Notebook with REST API patterns — for sources where API ingestion is the production path**
- **HubSpot** → API-first CRM. Notebook structured as if calling the HubSpot API, reads simulated JSON from Files.
- **Canvas** → REST API (Canvas LMS API). Same pattern as HubSpot.

### Demo vs Production

The only thing that changes between demo and production is the source connection. Everything downstream — silver, gold, Power BI — is identical.

| Source | Demo | Production |
|---|---|---|
| HubSpot | Notebook reads `Files/raw/hubspot/*.json` | `requests.get("https://api.hubapi.com/crm/v3/objects/contacts", ...)` |
| Canvas | Notebook reads `Files/raw/canvas/*.csv` | Canvas LMS REST API calls |
| Dynamics 365 | Copy Job from staged CSV | Copy Job via native Dataverse connector |
| Paradigm | Copy Job from staged CSV | Copy Job from scheduled SFTP/blob exports |

This is the strength of medallion architecture: the source layer is replaceable without touching anything else.

---

## 5. The Pipeline

### Step 1 — Local generation
```
python -m data_generator.main
```
Generates one weekend's worth of student lifecycle data with realistic mess (typo emails, inconsistent IDs across systems, timezone differences, nulls, duplicates, partial conversion rates).

### Step 2 — Upload to OneLake Files
All four source folders dropped into `Files/raw/<source>/` via OneLake Explorer.

In a production deployment, sources would be ingested directly. Documented as future improvement in README.

### Step 3 — Bronze ingestion (two patterns)

**Copy Job** for D365 and Paradigm:
- Standalone Copy Job items configured per source
- Read from `Files/raw/<source>/`, write Bronze Delta tables
- Incremental load mode enabled
- Invoked from Data Pipeline via Copy Job Activity

**Notebook (API style)** for HubSpot and Canvas:
- Code structured as if calling REST APIs: pagination, retry decorators, auth headers
- Reads from `Files/raw/<source>/` for the demo
- Comments call out where the production API endpoint would replace the file read

All bronze tables preserve source fidelity. Ingestion timestamp column added for lineage.

### Step 4 — Silver
Cleaning, type casting, and identity resolution across systems. One master student entity is produced by joining three sources. Eight silver tables:

| Table | Source |
|---|---|
| `silver_student` | D365 spine + HubSpot LEFT JOIN (contact_id) + Paradigm LEFT JOIN (email) |
| `silver_enrolment` | D365 — typed columns, `final_grade` null-coalesced from CSV empty string |
| `silver_marketing_source` | HubSpot — reference table pass-through |
| `silver_activity` | HubSpot — typed columns |
| `silver_course` | D365 — reference table pass-through |
| `silver_intake` | D365 — typed date columns |
| `silver_unit` | Paradigm — reference table pass-through |
| `silver_result` | Paradigm — joined to `silver_student` and `silver_unit` to add `student_number` and `course_code` |

### Step 5 — Gold
Star schema built around the two business questions in `reference/business_questions.md`. Integer surrogate keys on all dimensions for Power BI Direct Lake relationships.

**Dimensions (4):**

| Table | Grain | Key |
|---|---|---|
| `dim_student` | One row per student | `student_key` (integer surrogate) |
| `dim_course` | One row per course | `course_key` (integer surrogate) |
| `dim_intake` | One row per intake period | `intake_key` (integer surrogate) |
| `dim_marketing_source` | One row per acquisition channel | `marketing_source_key` (integer surrogate) |

**Facts (3):**

| Table | Grain | Answers |
|---|---|---|
| `fact_lead` | One row per HubSpot contact | Q1 — lead funnel, days to enrolment, source attribution |
| `fact_enrolment` | One row per course enrolment | Q1+Q2 — enrolment volume, completion rate, final grade |
| `fact_result` | One row per unit result | Q2 — academic performance by unit, grade distribution |

### Step 6 — Data quality
Row count sanity, null checks on critical columns, referential integrity, duplicate detection on natural keys.

### Step 7 — Email notification
Office 365 Outlook activity in the Data Pipeline sends success summary (row counts) or failure notification (which step failed + error message).

---

## 6. Power BI — Direct Lake Mode

Direct Lake is Fabric's headline feature and the reason this architecture uses Lakehouse rather than Warehouse.

**What it does:** Power BI reads gold Delta tables directly from OneLake. No import. No DirectQuery latency. Reports refresh as soon as the gold layer is updated.

The semantic model lives in the same workspace as the Lakehouse. RLS is not implemented in the demo.

---

## 7. Orchestration

A single Fabric Data Pipeline runs the end-to-end flow. The four bronze ingestion steps run in parallel (no inter-dependencies). Silver waits for all bronze. Gold waits for silver. Data quality runs last before email.

```
┌─ Copy Job (D365)              ─┐
├─ Copy Job (Paradigm)          ─┤
└─ Notebook 01_bronze_ingest    ─┘─▶ All bronze loaded
                │
                ▼
        Notebook 02_silver_clean
                │
                ▼
        Notebook 03_gold_model
                │
                ▼
    Notebook 04_data_quality_checks
                │
        ┌───────┴───────┐
        ▼               ▼
   On Success      On Failure
        │               │
        ▼               ▼
[Outlook: success] [Outlook: failure]
```

This replaces what would be Airflow/Step Functions in cloud-native projects. Fabric's native orchestrator means no separate compute to manage.

---

## 8. What's Out of Scope (For Honesty)

These would exist in a real production deployment but are deliberately not built in the demo:

- Real API ingestion from HubSpot/Canvas (code structure mirrors real ingestion)
- Real Dataverse connector for D365 (Copy Job from staged files used instead)
- CI/CD via Fabric Git integration (My Workspace doesn't support it)
- Dev/Test/Prod workspaces (single-workspace demo)
- Service principal auth (not available)
- Row-Level Security in Power BI (single-role demo)
- End-to-end incremental loads (Copy Jobs support it; notebooks use full refresh for simplicity)
- SCD Type 2 history on dim_student (would track attribute changes over time in production)
- Monitoring and alerting beyond success/failure email

Documented as next steps in the README to show awareness without overpromising.
