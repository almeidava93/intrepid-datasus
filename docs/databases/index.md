# DATASUS databases

DATASUS, the IT department of Brazil's Ministry of Health, publishes many national health
information systems on its public FTP (`ftp.datasus.gov.br/dissemin/publicos/`). Each
system records a different kind of event: an outpatient procedure, a hospital admission,
a death, a birth, a case of a notifiable disease. intrepid-datasus downloads them as they
are published and exposes each one as SQL tables.

## What is available

| System | What one record is | Status | Docs |
|---|---|---|---|
| **SIA/SUS** — *Sistema de Informações Ambulatoriais* | an outpatient procedure paid by SUS: consultations, exams, medicines, chemotherapy, dialysis, mental health care, ... | **Available** (all 14 file types, Jul/1994 onward) | [SIA overview](sia/index.md) |
| SIH/SUS — *Sistema de Informações Hospitalares* | a hospital admission paid by SUS (AIH) | Planned | — |
| SIM — *Sistema de Informações sobre Mortalidade* | a death certificate | Planned | — |
| SINASC — *Sistema de Informações sobre Nascidos Vivos* | a live birth | Planned | — |
| CNES — *Cadastro Nacional de Estabelecimentos de Saúde* | a health facility, its beds, equipment and professionals, per month | Planned | — |
| SINAN — *Sistema de Informação de Agravos de Notificação* | a case of a notifiable disease (dengue, tuberculosis, ...) | Planned | — |

Shared reference data used by several systems (states, SIGTAP procedures, ICD-10, CBO
occupations) is documented once, under [Reference data](../lookups/index.md).

!!! note "Status"
    *Planned* means the system is on the roadmap and the docs are laid out to receive it;
    it cannot be fetched yet. Contributors: see
    [Adding a database](../contributing/adding-a-database.md).

## How the systems connect

The systems are separate, with no common patient identifier you can use to link people
across them. They do share **codes**, which is what lets you compare and combine them:

| Shared code | What it identifies | In intrepid-datasus |
|---|---|---|
| IBGE municipality code (6 digits, no check digit) | where the facility is, where the patient lives | first 2 digits join [`ufs.ibge`](../lookups/index.md#ufs) |
| State (`uf`) | the state whose file a row came from | partition column `uf` on every table, joins [`ufs`](../lookups/index.md#ufs) |
| CNES code (7 digits) | a health facility | e.g. `pa.PA_CODUNI`, `apac.AP_CODUNI` |
| SIGTAP procedure code (10 digits) | a procedure, medicine or device, since 2008 | joins [`procedimentos`](../lookups/index.md#procedimentos) |
| ICD-10 code (no dot, `J189`) | a diagnosis or cause | joins [`cid10`](../lookups/index.md#cid10) |
| CBO code (6 digits) | a professional's occupation | joins [`ocupacoes`](../lookups/index.md#ocupacoes) |
| Competência (`YYYYMM`) | the month a record was processed | partition column `competencia` |

See [Key concepts](../concepts.md) for what each of these means.

## Choosing a system

| Question | System |
|---|---|
| How many consultations, exams, chemotherapy sessions, dialysis sessions, medicines dispensed? | SIA |
| How much SUS paid for outpatient care, and where? | SIA |
| How many hospital admissions, for what, how long, how much? | SIH (planned) |
| How many people died, of what? | SIM (planned) |
| How many babies were born, birth weight, prenatal visits? | SINASC (planned) |
| Which facilities exist, with which beds and equipment? | CNES (planned) |

SIA and SIH only cover care **paid by SUS**, not private care or care paid by health
insurance. Much of primary care is recorded in e-SUS APS (SISAB), which is not published
on the FTP, so SIA shows only part of it.
