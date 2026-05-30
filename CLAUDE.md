# JMC Student Data — Fabric Medallion Demo

Project-specific instructions. Read this together with the global `~/.claude/CLAUDE.md`.

---

## What This Project Is

A demonstration of consolidating student data from four operational source systems into a single Microsoft Fabric Lakehouse using medallion architecture, with Power BI on top via Direct Lake.

Built as a portfolio piece and conversation-starter for the **Data and Performance Analyst** role at JMC Academy (reporting to the Chief Customer Officer).

The audience for this repo is the hiring manager. Everything in it should be readable by a non-technical stakeholder at the README level, and by a senior data engineer at the code level.

---

## The Business Problem

JMC has student data scattered across four operational systems, each owning a different slice of the student lifecycle:

```
HubSpot       →  Pre-enrolment leads (marketing-driven)
Dynamics 365  →  Official student enrolment records
Paradigm      →  Academic results and grades
Canvas        →  Learning behaviour and engagement
```

No single source of truth. No ability to answer questions that cross systems.
This project builds the consolidation layer that makes those questions answerable.

---

## Key Constraints

1. **Fabric "My Workspace" only.** Owner has locked workspace creation. No Git integration, no Deployment Pipelines, no service principal auth.
2. **Notebooks in `/notebooks` are the source of truth.** Written locally in VS Code, committed to GitHub, manually copied into Fabric.
3. **Source data is simulated.** No real API access to any source. Realistic mess is baked into the generators.
4. **Single workspace logical separation only.** Dev/prod separation via folder structure inside the same Lakehouse.

---

## Conventions

**Python:** snake_case, type hints where useful, no over-engineering. Reasoning before code, simple over clever.

**SQL:** UPPERCASE keywords, snake_case identifiers.

**Table naming:**
```
bronze_<source>_<entity>     e.g. bronze_hubspot_contacts
silver_<entity>              e.g. silver_students
gold_<business_concept>      to be defined when data model is finalised
```

**Notebook naming:** `NN_<purpose>.ipynb` with two-digit prefix for execution order.

**File outputs (data generator):** dropped into `output/<source>/` locally. Format mirrors what each real source would export:
```
HubSpot       → JSON   (CRM is API-first)
Dynamics 365  → CSV    (Dataverse exports as CSV)
Paradigm      → CSV    (batch file exports from SIS)
Canvas        → CSV    (Canvas Data Portal exports as CSV)
```

---

## The Pipeline (End to End)

```
1. LOCAL    python -m data_generator.main
            → writes messy files to output/{hubspot,dynamics365,paradigm,canvas}/

2. UPLOAD   All 4 source folders uploaded to OneLake Files/raw/<source>/
            via OneLake Explorer or web UI (manual, no service principal)

3. FABRIC   Data Pipeline runs:
            ├ Copy Job → Dynamics 365 (Files → bronze_dynamics365_*)
            ├ Copy Job → Paradigm     (Files → bronze_paradigm_*)
            ├ Notebook 01a_ingest_hubspot  (API-style, Files → bronze_hubspot_*)
            ├ Notebook 01b_ingest_canvas   (API-style, Files → bronze_canvas_*)
            ├ Notebook 02_silver_clean
            ├ Notebook 03_gold_model
            ├ Notebook 04_data_quality
            └ Office 365 Outlook activity (email on success / failure)

4. POWER BI Semantic model on gold_* tables using Direct Lake mode
```

### Demo vs Reality

The only thing that changes between demo and production is the source connection. Silver, gold, and Power BI are identical.

| Source | Demo | Production |
|---|---|---|
| HubSpot | Notebook reads JSON from `Files/raw/hubspot/` | Notebook calls `api.hubapi.com/crm/v3/...` with bearer auth |
| Canvas | Notebook reads CSV from `Files/raw/canvas/` | Notebook calls Canvas LMS REST API |
| Dynamics 365 | Copy Job reads CSV from `Files/raw/dynamics365/` | Copy Job uses native Dataverse connector |
| Paradigm | Copy Job reads CSV from `Files/raw/paradigm/` | Copy Job reads scheduled SFTP/blob file exports |

### Why Hybrid Ingestion

| Source | Method | Why |
|---|---|---|
| Dynamics 365 | Copy Job | Native Dataverse connector in production |
| Paradigm | Copy Job | Batch file exports — Copy Job handles file → Delta cleanly |
| HubSpot | Notebook (API style) | API-first CRM, no Fabric Copy Job connector |
| Canvas | Notebook (API style) | LMS with REST API, no Fabric connector |

API-style notebooks structure code like real ingestion (pagination, tenacity retries, bearer auth) but read from staged OneLake Files for the demo. Comments call out where the production API endpoint would replace the file read.

---

## Don't Suggest

- Real API integrations. Everything is simulated.
- Service principal auth or Fabric Git integration. Not available.
- Three-workspace Dev/Test/Prod. Limited to My Workspace.
- Power BI Import mode. Use Direct Lake.
- Pytest against Fabric notebooks. Data quality lives in `04_data_quality_checks.ipynb`. Pytest is for the local data generator only.
- Heavy frameworks (no dbt, no Dagster, no Airflow). Fabric Data Pipelines handle orchestration natively.
- Reading files from laptop in Fabric notebooks. Notebooks run inside Fabric and only read from OneLake.

---

## Working Pattern

- Data model is built **first** in `reference/`. Code follows the model.
- Notebook logic developed locally as `.ipynb` files in `/notebooks` and copied into Fabric. GitHub is the source of truth.
- README and Loom demo video reserved for Sunday evening.
- `architecture.md` will be updated by Claude Code once the data model is finalised and the generator is built. Don't pre-fill speculative table names or schemas.
