# SIA/SUS — outpatient care

**SIA/SUS** (*Sistema de Informações Ambulatoriais do SUS*) records every outpatient
procedure that Brazil's public health system (SUS) pays for: consultations, lab tests and
imaging, emergency care, high-cost medicines, chemotherapy and radiotherapy, dialysis,
psychosocial care (CAPS), home care, and more. Facilities report what they did each month;
SIA validates it, pays for it, and DATASUS publishes the result, one file per state per
month, from Jul/1994.

**Not in SIA:** hospital admissions (SIH), deaths (SIM), births (SINASC), care not paid by
SUS. See [DATASUS databases](../index.md).

## Start here

1. Fetch one month of one small state and run your first queries:
   [Getting started](../../getting-started.md).
2. Read the five rules in [Pitfalls](data-notes.md). They prevent the most common wrong
   answers (counting rows instead of summing quantities, adding tables that contain the
   same records, ...).
3. Find the table for your question below, then open its page for every column.
4. Borrow a query from the [SQL cookbook](examples.md).

## How SIA records care

A facility reports its production on one of four kinds of form (*instrumentos de
registro*). Which form was used decides how much you know about the patient:

| Form | What it is | Patient data? | In `pa` as `PA_DOCORIG` |
|---|---|---|---|
| **BPA-C** — *Boletim de Produção Ambulatorial Consolidado* | monthly totals per procedure (e.g. "1,200 blood pressure checks") | **No** | `C` |
| **BPA-I** — *BPA Individualizado* | one line per patient appointment | Yes | `I` |
| **APAC** — *Autorização de Procedimento Ambulatorial* | a prior authorisation for a high-cost or long treatment (medicines, chemotherapy, dialysis, ...), valid up to 3 months | Yes, plus clinical details | `P` (main), `S` (secondary) |
| **RAAS** — *Registro das Ações Ambulatoriais de Saúde* | continuous care: CAPS (psychosocial) and home care | Yes | `B` (CAPS), `A` (home care) |

Every form ends up in the **PA** file (*Produção Ambulatorial*), the complete record of
what was paid. DATASUS also publishes the BPA-I, APAC and RAAS records again, in separate
**file types** that carry the patient and clinical details PA leaves out. That is why SIA
has one main table and many specialised ones.

## Which table do I need?

| I want to know... | Use | Coverage |
|---|---|---|
| How many procedures were done, how much was paid, by state, procedure, facility, month | [`pa`](pa.md) | 2008 → |
| The same, before 2008 (old procedure codes) | [`pa_legacy`](pa_legacy.md) | 1994–2007 |
| Distinct patients, date of birth, age in days/months, for individual appointments | [`bi`](bi.md) | 2008 → |
| Patients receiving each high-cost medicine (Componente Especializado) | [`am`](am.md) | 2008 → |
| Chemotherapy: cancer site, stage, purpose, treatment line | [`aq`](aq.md) | 2008 → |
| Radiotherapy: cancer site, stage, treated areas | [`ar`](ar.md) | 2008 → |
| Patients on chronic dialysis: type, vascular access, lab values | [`atd`](atd.md) (2014 →), [`an`](an.md) (2008–2014) | 2008 → |
| Chronic kidney disease before dialysis (stages 4–5) | [`amp`](amp.md) | Mar/2016 → |
| Surgery to create an arteriovenous fistula for dialysis | [`acf`](acf.md) | Aug/2014 → |
| Follow-up after bariatric surgery | [`abo`](abo.md) (2014 →), [`ab`](ab.md) (2008–2017) | 2008 → |
| Cataract and other eye surgery, eye injections, hearing aids, cardiac catheterisation, PET-CT, wheelchairs, ... | [`ad`](ad.md) | 2008 → |
| CAPS (psychosocial care): patients, diagnoses, drug use, homelessness | [`ps`](ps.md) | Nov/2012 → |
| Home care (*Melhor em Casa*) | [`sad`](sad.md) | 2012–2018 |
| Procedure, diagnosis, occupation or state **names** | [Reference data](../../lookups/index.md) | — |

When in doubt, start with **`pa`**: it has everything that was paid, with age, sex,
diagnosis and residence for the roughly half of procedures recorded per patient.

## Tables at a glance

| Table | One row is | Fetch with | Notes |
|---|---|---|---|
| [`pa`](pa.md) | one line of approved production | `-T pa` (default) | the main table |
| [`pa_legacy`](pa_legacy.md) | one line of production, old layout | `-T pa` with months before 2008 | old procedure codes, no SIGTAP |
| [`bi`](bi.md) | one patient appointment | `-T bi` | same rows as `pa` `I` |
| [`am`](am.md) | one medicine APAC in one month | `-T am` | [APAC](apac.md) |
| [`aq`](aq.md) | one chemotherapy APAC in one month | `-T aq` | [APAC](apac.md) |
| [`ar`](ar.md) | one radiotherapy APAC (per month until 2019, per treatment after) | `-T ar` | [APAC](apac.md) |
| [`ad`](ad.md) | one APAC of the "diverse" laudos in one month | `-T ad` | [APAC](apac.md) |
| [`atd`](atd.md) | one dialysis patient in one month | `-T atd` | [APAC](apac.md) |
| [`an`](an.md) | one dialysis patient in one month (before ATD) | `-T an` | [APAC](apac.md) |
| [`amp`](amp.md) | one pre-dialysis CKD patient in one month | `-T amp` | [APAC](apac.md) |
| [`acf`](acf.md) | one fistula surgery | `-T acf` | [APAC](apac.md) |
| [`ab`](ab.md) | one bariatric follow-up APAC in one month (old) | `-T ab` | [APAC](apac.md) |
| [`abo`](abo.md) | one bariatric follow-up APAC in one month | `-T abo` | [APAC](apac.md) |
| [`ps`](ps.md) | one action line of a CAPS patient's month | `-T ps` | [RAAS](raas.md) |
| [`sad`](sad.md) | one action line of a home-care patient's month | `-T sad` | [RAAS](raas.md) |

Every table also has a `_raw` twin (`pa_raw`, `bi_raw`, ...) with every column as text,
and two partition columns, `competencia` and `uf`; see
[Key concepts](../../concepts.md#how-data-is-stored).

The ten APAC tables share their `AP_` columns, described once on [APAC file types](apac.md);
the two RAAS tables share theirs on [RAAS file types](raas.md). How the tables join each
other, and which ones must never be added together, is on
[Joins and double counting](joins.md).

## Size

One month of PA for the whole country (May/2026) is ~2.7 GB to download, ~1 GB of
Parquet and ~71 million rows; a year is roughly 11–13 GB of Parquet. The specialised file
types are much smaller, except BI (~188 GB of `.dbc` for 2008–2026). Start small: one state,
one month.
