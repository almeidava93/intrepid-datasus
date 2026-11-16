# Joins and double counting

SIA publishes some records twice: once in `pa`, the complete record of what was paid, and
again in a specialised file type with more detail. This page shows how the tables join
each other and the lookup tables, and which ones must never be summed together.

## The one rule

!!! danger "Never add a specialised table to `pa`"
    Every row of `bi`, of the ten APAC tables and of the two RAAS tables is **already in
    `pa`**. Summing `pa` and, say, `aq` counts chemotherapy twice. Use `pa` for totals,
    and a specialised table for what `pa` lacks (patient identifiers, laudo fields, dates).

| Table | Same records as | Details |
|---|---|---|
| `bi` | `pa WHERE PA_DOCORIG = 'I'` (row for row) | [bi](bi.md#how-bi-relates-to-pa-double-counting) |
| `am` | `pa WHERE PA_DOCORIG = 'P' AND PA_TPFIN = '02'` | [am](am.md#how-am-relates-to-pa-double-counting) |
| `aq` | `pa WHERE PA_DOCORIG = 'P'`, procedures `030402`–`030408` | [aq](aq.md#how-aq-relates-to-pa-double-counting) |
| `ar` | `pa WHERE PA_DOCORIG = 'P'`, procedures `030401` | [ar](ar.md#how-ar-relates-to-pa-double-counting) |
| `ad` | some of `pa WHERE PA_DOCORIG = 'P'` | [ad](ad.md#how-ad-relates-to-pa-double-counting) |
| `atd` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` (Aug/2014 →) | [atd](atd.md#how-atd-relates-to-pa-double-counting) |
| `an` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` (→ May/2014) | [an](an.md#how-an-relates-to-pa-double-counting) |
| `ab` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID = '0301120056'`; also in `abo` from 2014 | [ab](ab.md#how-ab-relates-to-pa-double-counting) |
| `abo` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID = '0301120056'` | [abo](abo.md#how-abo-relates-to-pa-double-counting) |
| `acf` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID = '0418010030'` | [acf](acf.md#how-acf-relates-to-pa-double-counting) |
| `amp` | `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID IN ('0301130051', '0301130060')` | [amp](amp.md#how-amp-relates-to-pa-double-counting) |
| `ps` | `pa WHERE PA_DOCORIG = 'B'` | [ps](ps.md#how-ps-relates-to-pa-double-counting) |
| `sad` | `pa WHERE PA_DOCORIG = 'A'` | [sad](sad.md#how-sad-relates-to-pa-double-counting) |

An APAC row is one authorisation in one month; in `pa` the same APAC is one row per
procedure (`P` for the main one, `S` for each secondary one). See
[APAC file types](apac.md#what-one-row-is-and-the-link-to-pa) for the join.

## Joining an APAC table to `pa`

Join on the authorisation number, the month of care, and the partition columns:

```sql
SELECT a.AP_AUTORIZ, a.AP_VL_AP, p.PA_DOCORIG, p.PA_PROC_ID, p.PA_QTDAPR, p.PA_VALAPR
FROM aq a
JOIN pa p ON p.PA_AUTORIZ = a.AP_AUTORIZ AND p.PA_CMP = a.AP_CMP
         AND p.competencia = a.competencia AND p.uf = a.uf
WHERE a.competencia = 202605 AND a.uf = 'SC' AND p.PA_DOCORIG IN ('P', 'S');
```

Fetch both first (`datasus fetch -T pa,aq -s SC -f 202605`).

## Following a patient across tables

The APAC and RAAS tables carry the patient's national health card (CNS), **encoded by
DATASUS**: `AP_CNSPCN` in the APAC tables, `CNS_PAC` in `bi`, `ps` and `sad`. The same
encoding is used everywhere, so the same patient has the same value in `amp`, `acf` and
`atd` (kidney disease → fistula → dialysis), or in `aq` and `ar` (chemotherapy and
radiotherapy). It cannot be decoded or linked to other systems, and it is empty or a
placeholder (`{{{{{{{{{{{{{{{`) on many recent rows; check the table page before counting
patients.

## Join map

```text
                       ufs (uf)
                         │
pa ── PA_PROC_ID ──► procedimentos (codigo) ──► sigtap_rl_procedimento_* (CO_PROCEDIMENTO)
 │ ── PA_CIDPRI  ──► cid10 (codigo)
 │ ── PA_CBOCOD  ──► ocupacoes (codigo)
 └─── uf         ──► ufs (uf)

bi ── PROC_ID    ──► procedimentos (codigo)
 │ ── CIDPRI     ──► cid10 (codigo)
 │ ── CBOPROF    ──► ocupacoes (codigo)
 │ ── uf         ──► ufs (uf)
 └─── LEFT(MUNPAC, 2) ──► ufs (ibge)    patient's state of residence

am ── AP_PRIPAL  ──► procedimentos (codigo)    medicine
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ ──► pa (PA_AUTORIZ, same competencia and uf)

aq ── AP_PRIPAL  ──► procedimentos (codigo)    chemotherapy procedure (purpose, line)
 │ ── AP_CIDPRI, AQ_CIDINI1..3 ──► cid10 (codigo)    cancer, previous treatments
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ar ── AP_PRIPAL  ──► procedimentos (codigo)    radiotherapy procedure (site treated)
 │ ── AP_CIDPRI, AR_CIDTR1..3, AR_CIDINI1..3 ──► cid10 (codigo)    cancer, treated areas
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► aq (AP_CNSPCN)    same patient's chemotherapy
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ad ── AP_PRIPAL  ──► procedimentos (codigo)    procedure (grupo/subgrupo say what kind)
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

atd ── AP_PRIPAL ──► procedimentos (codigo)    dialysis procedure (haemodialysis, peritoneal)
 │ ── AP_CIDCAS  ──► cid10 (codigo)    the only diagnosis column filled
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► an (AP_CNSPCN)    same patient before Aug/2014
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

an ── AP_PRIPAL  ──► procedimentos (codigo)    dialysis procedure
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► atd (AP_CNSPCN)    same patient from Aug/2014
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ab ── AP_PRIPAL  ──► procedimentos (codigo)    always 0301120056 (follow-up after bariatric surgery)
 │ ── AB_PROCAIH ──► procedimentos (codigo)    the surgery, until Mar/2013
 │ ── AP_CIDCAS  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

abo ── AP_PRIPAL ──► procedimentos (codigo)    always 0301120056 (follow-up after bariatric surgery)
 │ ── AB_PROCAIH ──► procedimentos (codigo)    the surgery
 │ ── AP_CIDCAS, AP_CID_C1..C5, AP_CID_CO ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_AUTORIZ, AP_CMP ──► ab (same APACs, 2014-2017 and 2025)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

acf ── AP_PRIPAL ──► procedimentos (codigo)    always 0418010030 (arteriovenous fistula for haemodialysis)
 │ ── AP_CIDCAS  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► atd, an, ad (AP_CNSPCN)    same patient's dialysis, catheters and grafts
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

amp ── AP_PRIPAL ──► procedimentos (codigo)    0301130051 / 0301130060 (CKD stage 4 / 5, pre-dialysis)
 │ ── AP_CIDCAS  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► atd, acf, ad (AP_CNSPCN)    same patient's later dialysis, fistula, catheters
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ps ── PA_PROC_ID ──► procedimentos (codigo)    CAPS action (030108...)
 │ ── CIDPRI     ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(MUNPAC, 2) ──► ufs (ibge)
 │ ── CNS_PAC    ──► ad (AP_CNSPCN)    same patient's CAPS APACs until Dec/2012
 └─── CNES_EXEC, DT_ATEND, PA_PROC_ID ──► pa (PA_CODUNI, PA_CMP, PA_PROC_ID, PA_DOCORIG = 'B'; totals only)

sad ── PA_PROC_ID ──► procedimentos (codigo)    home-care action (0301050..., 0301010137, ...)
 │ ── CIDPRI, PA_CID ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(MUNPAC, 2) ──► ufs (ibge)
 └─── CNES_EXEC, DT_ATEND, PA_PROC_ID ──► pa (PA_CODUNI, PA_CMP, PA_PROC_ID, PA_DOCORIG = 'A'; totals only)
```

`pa_legacy` joins `ufs` the same way, but **not** the SIGTAP lookups: its procedure codes
(`PA_CODPRO`) belong to the old SIA table that SIGTAP replaced in Jan/2008.

## Sources

- **PA layout (2008 onward):** DATASUS, *Informe Técnico SIASUS* (Jul/2019), section 2.3,
  `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/Informe_Tecnico_SIASUS_2019_07.pdf`.
- **BI layout:** same Informe Técnico, section 5.2 (*Layout do arquivo de BPA-I*).
- **APAC layouts (AM, ...):** same Informe Técnico, section 3.4 (*Layout dos arquivos de APAC*;
  AD is 3.4.1, AM 3.4.2, AQ 3.4.4, AR 3.4.5, ATD 3.4.8, AN 3.4.3, AB in the same section). RAAS layouts (PS, SAD): section 4 (SAD 4.1, PS 4.2). ATD, AN and AB code lists: DATASUS *Layout da interface texto do APAC e do SIA*
  (Apr/2014), part 18 (ATD), part 09 (AN) and the bariatric parts 11 and 17 (AB; field positions of the old and new laudo).
- **SIGTAP:** the layout files (`*_layout.txt`) shipped inside each
  `TabelaUnificada_YYYYMM_v*.zip` at `ftp://ftp2.datasus.gov.br/public/sistemas/tup/downloads`,
  and the online browser at [sigtap.datasus.gov.br](http://sigtap.datasus.gov.br/).
- **General portal:** [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/).

DATASUS publishes no layout document for the 1994–2007 files on its FTP; see the caveat on
the [pa_legacy](pa_legacy.md) page.
