# Business Questions

The questions this project's data model is designed to answer. These drive every entity, every silver transformation, and every gold table. If an entity in the data model doesn't serve at least one of these questions, it doesn't belong in this project.

Questions are derived from the JMC Academy **Data and Performance Analyst** job description and the Chief Customer Officer's responsibilities.

---

## Q1 — The Lead-to-Enrolment Funnel

> **What does the lead-to-enrolment journey look like, and where are we losing people?**

**Why it matters**
This is the headline JD requirement: *"Design, build and maintain Power BI dashboards covering the full customer journey from lead to enrolment."* It's a marketing spend optimisation question. If 80% of paid social leads drop off between application and enrolment, that's a million-dollar problem to fix — and one no single source system can answer alone.

**Sources required**
- HubSpot — leads, activities, marketing source
- Dynamics 365 — official enrolment records

**The cross-system challenge**
A HubSpot Contact and a D365 Student are the same human, but neither system natively understands the other. The integration between them stores the HubSpot contact ID on the D365 Student record, which the silver layer uses for deterministic identity resolution. Walk-in students who never touched HubSpot have NULL contact IDs, requiring a fallback path.

**What the dashboard answers**
- Total leads → applications → offers → enrolled (funnel view)
- Conversion rate at each stage, sliced by marketing source
- Average time from first contact to enrolment
- Which marketing sources produce the highest volume of leads vs the highest conversion rate

---

## Q2 — Quality Over Quantity: Marketing Sources That Produce Successful Students

> **Which marketing sources produce students who actually succeed academically, not just enrol?**

**Why it matters**
Most marketing dashboards stop at conversion rate. A Chief Customer Officer needs to go one step further: if Channel A converts at 30% but those students drop out in their first term, and Channel B converts at 15% but those students graduate, then Channel B is actually the better channel. This question separates volume metrics from quality metrics.

**Sources required**
- HubSpot — marketing source
- Dynamics 365 — enrolment
- Paradigm — academic results, completion status

**The cross-system challenge**
Joins three systems through the student master identity. Paradigm has its own student identity separate from D365, requiring email-based resolution in silver. Tracking outcome (pass / fail / dropped) against original acquisition channel requires preserving the marketing source attribution all the way through to academic results.

**What the dashboard answers**
- Pass rate by marketing source
- Retention rate (term 1 → term 2) by marketing source
- Average grade by marketing source
- Which sources punch above their weight on quality

---

## How The Two Questions Work Together

```
Q1:  Lead   →  Enrolment                            HubSpot + D365
Q2:  Lead   →  Enrolment  →  Results                HubSpot + D365 + Paradigm
```

Two questions, three sources, covering the full journey from prospect to academic outcome. Every system earns its place. Every entity in the data model exists to serve at least one of these questions.

This is the consolidation problem the medallion architecture is designed to solve. Without integration across all three sources, neither question can be answered.

---

## Demo Scope

| Question | Demo deliverable |
|---|---|
| Q1 | Full Power BI page with funnel, conversion rates, source breakdown |
| Q2 | Full Power BI page with source-quality comparison, pass rates, retention |

---

## Future Enhancement — Engagement-Based Early Warning

A natural extension of this work is integrating Canvas LMS data to enable engagement-based predictions of academic outcomes — identifying at-risk students based on early-term engagement patterns (logins, submissions, time on page).

The medallion architecture is designed to accommodate this addition without restructuring:

- **Bronze:** Canvas becomes a fourth source, ingested via an API-style notebook
- **Silver:** A `silver_engagement` entity, with Canvas user identity resolved to the existing `silver_student` via email
- **Gold:** A new `fact_engagement_daily` table joins to existing `dim_student`, `dim_course`, `dim_date`
- **Power BI:** New report page correlating engagement metrics with academic outcomes

The proposed Q3 — *"Are students who engage early in Canvas more likely to pass, and can we identify at-risk students before it's too late?"* — moves the role from descriptive reporting into predictive, actionable insight. Out of scope for this demo to focus on the JD's headline requirement (customer journey from lead to enrolment), but a strong candidate for the first production iteration.

---

## Out of Scope (For Honesty)

Questions a Chief Customer Officer might genuinely want answered, but deliberately not in this demo:

- **Engagement / early warning** — see Future Enhancement above (Canvas integration)
- **Financial** — tuition revenue by source, cost-per-acquisition
- **Operational** — class sizes, room utilisation, staff workload
- **Compliance** — TEQSA reporting, government data submissions
- **Alumni** — post-graduation employment, alumni engagement

These would extend the model in a real deployment but are not needed to demonstrate the consolidation pattern this project is built to prove.