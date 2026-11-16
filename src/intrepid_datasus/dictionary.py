"""Column descriptions for each SIA file type, one dict per layout (era).

Each era in ``catalog.REGISTRY`` points at one of these dicts. Start a new file type's
dict from ``PARTITION`` (the columns every table gets from the store layout).

Official, complete documentation: https://datasus.saude.gov.br/transferencia-de-arquivos/
(SIA → Documentação → Informe Técnico / layout PA).
"""

# Columns added by the local store, present in every SIA table.
PARTITION = {
    "competencia": "Partition: month of the file (YYYYMM).",
    "uf": "Partition: state of the file (SP, RJ, ...).",
    "_ARQUIVO_ORIGEM": "Original DATASUS file this row came from (e.g. PASP2605a.dbc).",
}

# ------------------------------------------------------------------- PA
# Text columns cast to numbers in the typed views (pa, pa_legacy); missing ones are skipped.
PA_QUANTITY_COLS = ("PA_QTDPRO", "PA_QTDAPR")
PA_VALUE_COLS = (
    "PA_VALPRO", "PA_VALAPR", "PA_DIF_VAL", "NU_VPA_TOT", "NU_PA_TOT",
    "PA_VL_CF", "PA_VL_CL", "PA_VL_INC", "PA_VL_CRD",
)

PA_COMMON = {
    **PARTITION,
    "competencia": "Partition: month of the file (YYYYMM). Normally equals PA_MVM (processing month).",
    "uf": "Partition: state of the file (SP, RJ, ...). Same as the facility's state.",
    "PA_CODUNI": "Facility code (CNES; 7 digits from 2008, 6 before).",
    "PA_GESTAO": "Managing authority: state (UF code + 0000) or municipality (IBGE code).",
    "PA_CONDIC": "Management condition code (state vs municipal management; see DATASUS docs).",
    "PA_UFMUN": "Municipality of the FACILITY (IBGE, 6 digits). First 2 digits = state.",
    "PA_DOCORIG": "Source document: C = BPA consolidated (no patient data), I = BPA individual, "
                  "P = APAC main procedure, S = APAC secondary procedure, "
                  "A = RAAS home care, B = RAAS psychosocial. Check DATASUS docs before relying on it.",
    "PA_TIPPRE": "Provider type.",
    "PA_QTDPRO": "Quantity submitted (number). Sum this, don't count rows.",
    "PA_QTDAPR": "Quantity approved (number). Sum this, don't count rows.",
    "PA_VALPRO": "Value submitted, R$ (number, nominal — not inflation adjusted).",
    "PA_VALAPR": "Value approved, R$ (number, nominal — not inflation adjusted).",
    "PA_CIDPRI": "Main diagnosis, ICD-10. '0000' = not informed.",
    "PA_CIDSEC": "Secondary diagnosis, ICD-10.",
    "PA_INDICA": "Approval status indicator (see DATASUS docs for codes).",
    "PA_CODOCO": "Occurrence / rejection code.",
}

PA = {
    **PA_COMMON,
    "PA_REGCT": "Contract rule (regra contratual).",
    "PA_INCOUT": "Increment code: other.",
    "PA_INCURG": "Increment code: urgency.",
    "PA_TPUPS": "Facility type (e.g. 02 = health centre, 05 = general hospital, 70 = CAPS).",
    "PA_MN_IND": "Facility is maintained by a body (M) or independent (I).",
    "PA_CNPJCPF": "Facility tax ID (CNPJ/CPF).",
    "PA_CNPJMNT": "Maintaining body's CNPJ.",
    "PA_CNPJ_CC": "CNPJ for the transfer of funds (cessão de crédito).",
    "PA_MVM": "Processing month (YYYYMM).",
    "PA_CMP": "Month the care was delivered (YYYYMM). Can be earlier than PA_MVM for late reports.",
    "PA_PROC_ID": "Procedure code, SIGTAP table (10 digits). Group = first 2 digits.",
    "PA_TPFIN": "Funding type (01 = primary care PAB, 02 = pharmacy, 04 = FAEC, 06 = MAC medium/high complexity).",
    "PA_SUBFIN": "Funding subtype.",
    "PA_NIVCPL": "Complexity (1 = primary care, 2 = medium, 3 = high, 0 = not applicable).",
    "PA_AUTORIZ": "Authorisation number (APAC/RAAS).",
    "PA_CNSMED": "Professional's national health card (CNS).",
    "PA_CBOCOD": "Professional's occupation code (CBO).",
    "PA_MOTSAI": "Reason for discharge/termination (APAC).",
    "PA_OBITO": "Death (1 = yes).",
    "PA_ENCERR": "Closure (1 = yes).",
    "PA_PERMAN": "Continuing (1 = yes).",
    "PA_ALTA": "Discharge (1 = yes).",
    "PA_TRANSF": "Transfer (1 = yes).",
    "PA_CIDCAS": "Associated cause, ICD-10.",
    "PA_CATEND": "Type of care (01 = elective, 02 = urgent, ...).",
    "PA_IDADE": "Patient age in years (text). '999' = not informed.",
    "IDADEMIN": "Minimum age allowed for the procedure.",
    "IDADEMAX": "Maximum age allowed for the procedure.",
    "PA_FLIDADE": "Age compatibility flag.",
    "PA_SEXO": "Patient sex (M, F; '0' = not informed — always for PA_DOCORIG = C).",
    "PA_RACACOR": "Race/colour (01 white, 02 black, 03 brown, 04 yellow, 05 indigenous, 99/00 not informed).",
    "PA_MUNPCN": "Municipality where the PATIENT lives (IBGE). '999999' = not informed.",
    "PA_UFDIF": "Patient lives in another state (1 = yes).",
    "PA_MNDIF": "Patient lives in another municipality (1 = yes).",
    "PA_DIF_VAL": "Difference between submitted and approved value, R$ (number).",
    "NU_VPA_TOT": "Total value of the authorisation, R$ (number).",
    "NU_PA_TOT": "Total value of the procedure, R$ (number).",
    "PA_FLQT": "Quantity check flag.",
    "PA_FLER": "Error flag.",
    "PA_ETNIA": "Indigenous ethnicity code.",
    "PA_VL_CF": "Federal complement value, R$ (number).",
    "PA_VL_CL": "Local complement value, R$ (number).",
    "PA_VL_INC": "Increment value, R$ (number).",
    "PA_VL_CRD": "Credit value, R$ (number). Present in recent files only.",
    "PA_SRV_C": "Specialised service/classification code.",
    "PA_INE": "Health team identifier (INE).",
    "PA_NAT_JUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table).",
    "PA_FNTORC": "Budget source.",
}

PA_LEGACY = {
    **PA_COMMON,
    "PA_DATREF": "Reference month (YYMM).",
    "PA_CODPRO": "Procedure code, old SIA table (7-8 digits; not SIGTAP).",
    "PA_CODESP": "Specialty code.",
    "PA_TIPPRO": "Procedure type.",
    "PA_TIPATE": "Type of care.",
    "PA_FXETAR": "Patient age band.",
    "PA_DATPR": "Processing month (YYMM).",
    "PA_MUNAT": "Municipality of care.",
    "PA_NUMAPA": "APAC number.",
    "PA_MORFOL": "Tumour morphology (oncology).",
}

# ------------------------------------------------------------------- BI
# BPA Individualizado (BPA-I), files BI<UF><YY><MM>.dbc, Jan/2008 onward. One layout; NAT_JUR
# was added in Jul/2016 (NULL before). Source: DATASUS, "Informe Técnico SIASUS" (Jul/2019),
# section 5.2 "Layout do arquivo de BPA-I: BIUFAAMM.DBF",
# ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/Informe_Tecnico_SIASUS_2019_07.pdf
# Code lists noted below were checked against the AC May/2026 file. BI rows are the PA rows
# with PA_DOCORIG = 'I' (same rows, quantities and values), so never sum bi and pa together.
BI_QUANTITY_COLS = ("QT_APRES", "QT_APROV")
BI_VALUE_COLS = ("VL_APRES", "VL_APROV")

BI = {
    **PARTITION,
    "competencia": "Partition: month of the file (YYYYMM). Equals DT_PROCESS (processing month).",
    "uf": "Partition: state of the file (SP, RJ, ...). Same as the facility's state.",
    "_ARQUIVO_ORIGEM": "Original DATASUS file this row came from (e.g. BIAC2605.dbc, BISP2605_1.dbc).",
    "CODUNI": "Facility code (CNES, 7 digits). Same as PA_CODUNI.",
    "GESTAO": "Managing authority: UF code + IBGE municipality code of the manager, or UF + '0000' "
              "when the facility is under state management.",
    "CONDIC": "Type of management the state/municipality is qualified for (values seen: EP, PG).",
    "UFMUN": "Municipality of the FACILITY (IBGE, 6 digits). First 2 digits = state.",
    "TPUPS": "Facility type, CNES codes (e.g. 02 = health centre, 05 = general hospital, "
             "36 = specialised clinic, 39 = diagnostic unit, 73 = emergency unit).",
    "TIPPRE": "Provider type.",
    "MN_IND": "Facility is maintained by a body (M) or independent (I).",
    "CNPJCPF": "Facility tax ID (CNPJ).",
    "CNPJMNT": "Maintaining body's CNPJ, or zeros if none.",
    "CNPJ_CC": "CNPJ of the body paid for the production by transfer of credit (cessão de crédito), or zeros.",
    "DT_PROCESS": "Processing month (YYYYMM). Same as PA_MVM.",
    "DT_ATEND": "Month the care was delivered (YYYYMM). Can be earlier than DT_PROCESS for late reports. "
                "Same as PA_CMP.",
    "PROC_ID": "Procedure code, SIGTAP table (10 digits). Group = first 2 digits. Joins procedimentos.",
    "TPFIN": "Funding type (01 = primary care PAB, 04 = FAEC, 05 = MAC incentive, "
             "06 = MAC medium/high complexity, 07 = health surveillance).",
    "SUBFIN": "Funding subtype.",
    "COMPLEX": "Complexity (1 = primary care, 2 = medium, 3 = high, 0 = not applicable).",
    "AUTORIZ": "BPA-I authorisation number (format UFAATsssssssd). Optional in BPA-I and not checked, "
               "so often blank or repeated: do not use it as a key.",
    "CNSPROF": "Professional's national health card (CNS) number.",
    "CBOPROF": "Professional's occupation code (CBO, 6 characters). Joins ocupacoes.",
    "CIDPRI": "Main diagnosis, ICD-10 (no dot, e.g. 'I10', 'E119'). '0000' = not informed. Joins cid10.",
    "CATEND": "Type of care (caráter de atendimento): 01 = elective, 02 = urgent, 03-06 = work/traffic "
              "accident and other external causes.",
    "CNS_PAC": "Patient's national health card (CNS), ENCODED by DATASUS (not the real number); "
               "empty on about half the rows. Same value = same patient within the data; "
               "cannot be linked to other systems.",
    "DTNASC": "Patient's date of birth (YYYYMMDD).",
    "TPIDADEPAC": "Unit of IDADEPAC, computed from the date of birth: 2 = days, 3 = months, "
                  "4 = years, 5 = 100 years or more (age = 100 + IDADEPAC), 9 = not informed.",
    "IDADEPAC": "Patient age (2 characters), in the unit given by TPIDADEPAC.",
    "SEXOPAC": "Patient sex (M, F; I = not informed, rare).",
    "RACACOR": "Race/colour (01 white, 02 black, 03 brown, 04 yellow, 05 indigenous, 99 not informed).",
    "MUNPAC": "Municipality where the PATIENT lives (IBGE, 6 digits); the facility's municipality "
              "when the patient is not identified.",
    "QT_APRES": "Quantity submitted (number). Sum this, don't count rows.",
    "QT_APROV": "Quantity approved (number). Sum this, don't count rows.",
    "VL_APRES": "Value submitted, R$ (number, nominal — not inflation adjusted).",
    "VL_APROV": "Value approved, R$ (number, nominal — not inflation adjusted).",
    "UFDIF": "Patient lives in another state than the facility (0 = same, 1 = different).",
    "MNDIF": "Patient lives in another municipality than the facility (0 = same, 1 = different).",
    "ETNIA": "Indigenous ethnicity code (Portaria SAS 508/2010, annex I); only when RACACOR = 05, "
             "from Oct/2010.",
    "NAT_JUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table). From Jul/2016; NULL "
               "before, except in the Dec/2011 files (the column was there that month only).",
}

# ------------------------------------------------------------------- APAC (shared)
# Columns shared by the APAC file types (AM, AQ, AR, AD, ATD, AN, ACF, AMP, ...): the APAC
# header, patient and validity fields, all prefixed AP_. Same names, order and meaning in
# every APAC layout. Source: DATASUS, "Informe Técnico SIASUS" (Jul/2019), section 3.4
# "Layout dos arquivos de APAC" (3.4.1 AD, 3.4.2 AM, ...),
# ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/Informe_Tecnico_SIASUS_2019_07.pdf
# AP_NATJUR is not in the 2019 document for every type but is in the files from Jul/2016.
# ABO renames a few of these (AP_TPPRE, AP_TPATEND, AP_DTOOCOR, AP_APACAN): pass them to
# apac() with their own descriptions and drop the originals with ``without``.
# What an APAC is (authorisation, validity, continuation, patient): docs/tables/apac.md.
APAC_QUANTITY_COLS: tuple[str, ...] = ()  # APAC files carry no quantity column
APAC_VALUE_COLS = ("AP_VL_AP",)

APAC_COMMON = {
    "AP_MVM": "Processing month (YYYYMM). Normally equals competencia. Same as PA_MVM.",
    "AP_CONDIC": "Type of management the state/municipality is qualified for (values seen: EP, PG).",
    "AP_GESTAO": "Managing authority: UF code + IBGE municipality code of the manager, or UF + '0000' "
                 "when the facility is under state management.",
    "AP_CODUNI": "Facility code (CNES, 7 digits) of the facility that delivered the care. Same as PA_CODUNI.",
    "AP_AUTORIZ": "APAC number (13 digits, format UFAATsssssssd: state, year, type, sequence, check digit). "
                  "Identifies one authorisation; the same number comes back every month the APAC is "
                  "valid. Joins PA_AUTORIZ.",
    "AP_CMP": "Month the care was delivered (competência, YYYYMM). Can be earlier than AP_MVM. "
              "Same as PA_CMP.",
    "AP_PRIPAL": "Main procedure of the APAC, SIGTAP code (10 digits). Joins procedimentos.",
    "AP_VL_AP": "Approved value, R$ (number, nominal — not inflation adjusted). For the whole APAC per "
                "DATASUS; see the table page before summing.",
    "AP_UFMUN": "Municipality of the FACILITY (IBGE, 6 digits). First 2 digits = state.",
    "AP_TPUPS": "Facility type, CNES codes (e.g. 05 = general hospital, 36 = specialised clinic, "
                "43 = pharmacy).",
    "AP_TIPPRE": "Provider type.",
    "AP_MN_IND": "Facility is maintained by a body (M) or independent (I).",
    "AP_CNPJCPF": "Facility tax ID (CNPJ).",
    "AP_CNPJMNT": "Maintaining body's CNPJ, or zeros if none.",
    "AP_CNSPCN": "Patient's national health card (CNS), ENCODED by DATASUS (not the real number). "
                 "Same value = same patient within the data; cannot be linked to other systems. "
                 "Can be empty or a placeholder in some types (AQ, AR, AD): see the table page.",
    "AP_COIDADE": "Unit of AP_NUIDADE: 2 = days, 3 = months, 4 = years, 5 = 100 years or more "
                  "(age = 100 + AP_NUIDADE), 9 = not informed.",
    "AP_NUIDADE": "Patient age (2 characters), in the unit given by AP_COIDADE.",
    "AP_SEXO": "Patient sex (M, F).",
    "AP_RACACOR": "Race/colour (01 white, 02 black, 03 brown, 04 yellow, 05 indigenous, 99 not informed).",
    "AP_MUNPCN": "Municipality where the PATIENT lives (IBGE, 6 digits).",
    "AP_UFNACIO": "Patient nationality code (010 = Brazilian).",
    "AP_CEPPCN": "Postcode (CEP) of the patient's address.",
    "AP_UFDIF": "Patient lives in another state than the facility (0 = same, 1 = different).",
    "AP_MNDIF": "Patient lives in another municipality than the facility (0 = same, 1 = different). "
                "Unreliable (always 1 in AM, AQ, AR, AD, ATD, AN and AB): compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_DTINIC": "Start of the APAC's validity period (YYYYMMDD).",
    "AP_DTFIM": "End of the APAC's validity period (YYYYMMDD); up to 3 months after AP_DTINIC.",
    "AP_TPATEN": "APAC type of care (tipo de atendimento / laudo); fixed per file type.",
    "AP_TPAPAC": "1 = initial APAC (first month), 2 = continuation (later months of the same "
                 "authorisation), 3 = single (one month only).",
    "AP_MOTSAI": "Reason for exit or continuation (motivo de saída/permanência): 1x = discharge "
                 "(11 cured, 12 improved, 14 on request, 15 with return for follow-up, 16 evasion, 18 other), "
                 "2x = continues (21 nature of the disease, 22 complication, 26 change of procedure, "
                 "28 other reasons), 31 = transfer, 4x = death, 51 = closed administratively.",
    "AP_OBITO": "Death (1 = yes).",
    "AP_ENCERR": "APAC closed (1 = yes).",
    "AP_PERMAN": "Patient continues (1 = yes).",
    "AP_ALTA": "Discharge (1 = yes).",
    "AP_TRANSF": "Transfer (1 = yes).",
    "AP_DTOCOR": "Date of the event (death, discharge, ...) that replaces the end of validity (YYYYMMDD).",
    "AP_CODEMI": "Issuing body (órgão emissor) that authorised the APAC: 'E' + state IBGE code + "
                 "'0000001' (or another 7-digit suffix) = state health secretariat; 'M' + IBGE municipality "
                 "code + '0001' = municipal health secretariat; 'S' and 'U' + 9 digits are other "
                 "authorising bodies.",
    "AP_CATEND": "Type of care (caráter de atendimento): 01 = elective, 02 = urgent, 03-06 = work/traffic "
                 "accident and other external causes.",
    "AP_APACANT": "Number of the previous APAC (the one this one continues), or zeros. Continuation "
                  "months normally keep the same AP_AUTORIZ instead, so this is mostly zeros.",
    "AP_UNISOL": "CNES code of the facility that requested the APAC (zeros when not informed).",
    "AP_DTSOLIC": "Date the APAC was requested (YYYYMMDD).",
    "AP_DTAUT": "Date the APAC was authorised (YYYYMMDD).",
    "AP_CIDCAS": "Associated cause, ICD-10 (no dot), or '0000'. Joins cid10.",
    "AP_CIDPRI": "Main diagnosis, ICD-10 (no dot, e.g. 'M058'). Joins cid10.",
    "AP_CIDSEC": "Secondary diagnosis, ICD-10 (no dot), or '0000'. Joins cid10.",
    "AP_ETNIA": "Indigenous ethnicity code (Portaria SAS 508/2010, annex I); only when AP_RACACOR = 05.",
    "AP_NATJUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table). From Jul/2016; NULL "
                 "before, except in the Dec/2011 files (every APAC type had the column that month only).",
}


def apac(code: str, own: dict[str, str], without: tuple[str, ...] = ()) -> dict[str, str]:
    """Dictionary of an APAC file type: partition columns, the shared AP_ columns (minus
    ``without``) and the type's own columns (``own``, which may also override AP_ ones)."""
    return {
        **PARTITION,
        "competencia": "Partition: month of the file (YYYYMM). Equals AP_MVM (processing month).",
        "uf": "Partition: state of the file (SP, RJ, ...). Same as the facility's state.",
        "_ARQUIVO_ORIGEM": f"Original DATASUS file this row came from (e.g. {code}SP2605.dbc).",
        **{k: v for k, v in APAC_COMMON.items() if k not in without},
        **own,
    }


# ------------------------------------------------------------------- AM
# APAC de Medicamentos (Componente Especializado da Assistência Farmacêutica), files
# AM<UF><YY><MM>.dbc, Jan/2008 onward. One layout (AP_NATJUR added Jul/2016). Source:
# "Informe Técnico SIASUS" (Jul/2019), section 3.4.2 "Layout do arquivo de APAC de
# medicamentos: AMUFAAMM.DBF" (URL above).
AM_QUANTITY_COLS = APAC_QUANTITY_COLS
AM_VALUE_COLS = APAC_VALUE_COLS

AM = apac("AM", {
    "AP_PRIPAL": "Main medicine of the APAC, SIGTAP procedure code (10 digits, always 0604...). "
                 "Secondary medicines of the same APAC are only in pa (PA_DOCORIG = 'S'). Joins procedimentos.",
    "AP_VL_AP": "Approved value of the whole APAC, R$ (number, nominal): main plus secondary medicines, "
                "= SUM(PA_VALAPR) of its pa rows. 0 on about 9 rows in 10, mostly medicines with no "
                "SIGTAP price (bought centrally by the Ministry): not a measure of spending.",
    "AP_TPATEN": "APAC type of care; always 06 (medicines) in AM.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AM (wrong): "
                "compare AP_MUNPCN with AP_UFMUN instead.",
    "AM_PESO": "Patient weight in kg.",
    "AM_ALTURA": "Patient height in cm.",
    "AM_TRANSPL": "Patient has had a transplant (S = yes, N = no).",
    "AM_QTDTRAN": "Number of transplants.",
    "AM_GESTANT": "Patient is pregnant (S = yes, N = no).",
})


# ------------------------------------------------------------------- AQ
# APAC de Quimioterapia (oncology: chemotherapy and hormone therapy), files AQ<UF><YY><MM>.dbc,
# Jan/2008 onward. One layout: AP_NATJUR added Jul/2016 and AQ_MED01..AQ_MED10 added Jan/2021
# (empty until Feb/2022), both NULL before. Source: "Informe Técnico SIASUS" (Jul/2019),
# section 3.4.4 "Layout do arquivo de APAC de quimioterapia: AQUFAAMM.DBF" (URL above).
# AQ_MED01..10 are not in that document; their description comes from the data.
# Values and fill rates: docs/tables/aq.md.
AQ_QUANTITY_COLS = APAC_QUANTITY_COLS
AQ_VALUE_COLS = APAC_VALUE_COLS

AQ = apac("AQ", {
    "AP_PRIPAL": "Chemotherapy/hormone therapy procedure, SIGTAP code (10 digits, 030402 to 030408). The "
                 "6-digit prefix is the PURPOSE: 030402 palliative, 030403 temporary disease control, "
                 "030404 prior (neoadjuvant), 030405 adjuvant, 030406 curative (all adult), 030407 children "
                 "and adolescents, 030408 special procedures. The name also gives the tumour, often the "
                 "stage and the line ('1ª LINHA'). Joins procedimentos.",
    "AP_VL_AP": "Approved value of the APAC in this month, R$ (number, nominal) = SUM(PA_VALAPR) of its "
                "pa rows (main + secondary procedures). 0 on about 1 row in 10 (rejected or not paid).",
    "AP_TPATEN": "APAC type of care; always 03 (chemotherapy) in AQ.",
    "AP_TPAPAC": "1 = first month of an APAC, 2 = later months (4 and 3 are rare). A new APAC is issued "
                 "every 3 months of ongoing treatment and is 1 again: 1 does NOT mean a new patient "
                 "(see AQ_CONTTR).",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AQ (wrong): "
                "compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CIDPRI": "Cancer diagnosis, ICD-10 (no dot, e.g. 'C504'); always filled (C or D codes). The "
                 "reliable cancer CID of AQ. Joins cid10.",
    "AP_CIDSEC": "Secondary ICD-10, or '0000' (about 5 rows in 6). When filled it mostly repeats AP_CIDPRI "
                 "(or a metastasis code such as C795). Joins cid10.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS. Empty (NULL) or the placeholder '{{{{{{{{{{{{{{{' on a "
                 "share of rows that grows from 2024 (about 15% of SP in Jul/2025, 95% of AC from Apr/2026): "
                 "exclude both before counting or following patients.",
    "AQ_CID10": "Tumour topography, ICD-10 (no dot). Equals AP_CIDPRI when filled; mostly empty from "
                "Mar/2022 (about 1 row in 6). Use AP_CIDPRI. Joins cid10.",
    "AQ_LINFIN": "Regional lymph nodes invaded: S = yes, N = no, 3 = not assessable.",
    "AQ_ESTADI": "Stage (UICC): 0, 1, 2, 3 or 4; empty on about 1 row in 8 (e.g. leukaemias).",
    "AQ_GRAHIS": "Histopathological grade, 2 characters, loosely coded: digits (1-4, also 0, 9 and 10-12), "
                 "G1-G4/GX, X, '-', ... Not a clean code; use with care.",
    "AQ_DTIDEN": "Date the cancer was identified by pathology (diagnosis date, YYYYMMDD).",
    "AQ_TRANTE": "Previous treatments: S = yes, N = no; '0' (not informed) on most rows since 2013.",
    "AQ_CIDINI1": "ICD-10 of the 1st previous treatment, or empty. Joins cid10.",
    "AQ_DTINI1": "Start date of the 1st previous treatment (YYYYMMDD), or empty/zeros.",
    "AQ_CIDINI2": "ICD-10 of the 2nd previous treatment, or empty.",
    "AQ_DTINI2": "Start date of the 2nd previous treatment (YYYYMMDD), or empty/zeros.",
    "AQ_CIDINI3": "ICD-10 of the 3rd previous treatment, or empty.",
    "AQ_DTINI3": "Start date of the 3rd previous treatment (YYYYMMDD), or empty/zeros.",
    "AQ_CONTTR": "Continuation of a treatment already under way: S = yes, N = no (a new treatment).",
    "AQ_DTINTR": "Start date of the requested treatment (YYYYMMDD). Same across the successive APACs of one "
                 "treatment; a new date means a new treatment. Some typos (years like 4026).",
    "AQ_ESQU_P1": "Treatment scheme (drug or regimen name or abbreviation), first 5 characters, free text "
                  "(e.g. 'ANAST' + 'ROZOL', 'FOLFO' + 'X', 'TMX').",
    "AQ_TOTMPL": "Total months of treatment planned (3 digits, e.g. '060').",
    "AQ_TOTMAU": "Total months authorised so far (3 digits); grows with each APAC of the treatment.",
    "AQ_ESQU_P2": "Treatment scheme, last 10 characters (continues AQ_ESQU_P1); free text, mixed case.",
    **{f"AQ_MED{i:02d}": f"Antineoplastic drug {i} of the scheme, 3-digit code of SIA's oncology drug list "
                         f"(e.g. 011 anastrozole, 037 tamoxifen, 090 hydroxyurea, 105 imatinib: inferred "
                         f"from AQ_ESQU, no official table in the package). Column from Jan/2021, filled "
                         f"from Mar/2022; empty when the scheme has fewer drugs." for i in range(1, 11)},
})



# ------------------------------------------------------------------- AR
# APAC de Radioterapia (oncology), files AR<UF><YY><MM>.dbc, Jan/2008 onward. One layout:
# AP_NATJUR added Jul/2016 (NULL before). Source: "Informe Técnico SIASUS" (Jul/2019), section
# 3.4.5 "Layout do arquivo de APAC de radioterapia: ARUFAAMM.DBF" (URL above); AR_SMRD has no
# description there. The laudo fields AR_CID10 .. AR_DTINTR are those of AQ. In 2019 SIGTAP
# replaced the per-field/per-session radiotherapy codes by one code per treatment and body
# site (from May/2019): since then each row is a whole treatment (AP_TPAPAC = 3) and AR_NUMC*, the 2nd and
# 3rd treated area and their dates are empty. Values and fill rates: docs/tables/ar.md.
AR_QUANTITY_COLS = APAC_QUANTITY_COLS
AR_VALUE_COLS = APAC_VALUE_COLS

AR = apac("AR", {
    "AP_PRIPAL": "Radiotherapy procedure, SIGTAP code (10 digits, always 030401...). Until 2019 a technique "
                 "billed per field, insertion or session (0304010090 cobalt therapy per field, 0304010294 "
                 "linear accelerator per field, 0304010073 HDR brachytherapy per insertion, ...); since 2019 "
                 "one code per treatment and site (0304010413 breast, 0304010456 prostate, 0304010537 "
                 "metastases/myeloma, ...). Joins procedimentos.",
    "AP_VL_AP": "Approved value of the APAC in this month, R$ (number, nominal) = SUM(PA_VALAPR) of its pa "
                "rows (main + secondary procedures). Since 2019 the price of the whole treatment.",
    "AP_TPATEN": "APAC type of care; always 04 (radiotherapy) in AR.",
    "AP_TPAPAC": "1 = first month of an APAC, 2 = later months, 3 = single APAC (the whole treatment, "
                 "billed once). Always 3 since 2020 (new procedures from May/2019): one row per treatment.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AR (wrong): "
                "compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CIDPRI": "Cancer diagnosis, ICD-10 (no dot, e.g. 'C509'); always filled. The cancer of the APAC "
                 "(C79x/C77x for metastases treated). Joins cid10.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS. Empty (NULL) or the placeholder '{{{{{{{{{{{{{{{' on a "
                 "share of rows that grows from mid-2024 and jumps from Nov/2025 (95% of all rows in "
                 "Aug/2026, 98-100% in SC and SP): exclude both before counting or following patients.",
    "AR_SMRD": "Not described in the layout document; always empty.",
    "AR_CID10": "Tumour topography, ICD-10 (no dot). Usually equals AP_CIDPRI; empty on about 1 row in 4. "
                "Use AP_CIDPRI. Joins cid10.",
    "AR_LINFIN": "Regional lymph nodes invaded: S = yes, N = no, 3 = not assessable.",
    "AR_ESTADI": "Stage (UICC): 0, 1, 2, 3 or 4; empty on about 1 row in 5 (benign disease, skin, ...).",
    "AR_GRAHIS": "Histopathological grade, 2 characters, loosely coded: digits (0-12), 00-06, G1-G4/GX, X, XX, "
                 "II, ... Not a clean code; use with care.",
    "AR_DTIDEN": "Date the cancer was identified by pathology (diagnosis date, YYYYMMDD).",
    "AR_TRANTE": "Previous treatments: S = yes, N = no; empty on about 1 row in 5 (and C on a few 2009-2012 rows).",
    "AR_CIDINI1": "ICD-10 of the 1st previous treatment, or empty. Joins cid10.",
    "AR_DTINI1": "Start date of the 1st previous treatment (YYYYMMDD), or empty/zeros.",
    "AR_CIDINI2": "ICD-10 of the 2nd previous treatment, or empty.",
    "AR_DTINI2": "Start date of the 2nd previous treatment (YYYYMMDD), or empty/zeros.",
    "AR_CIDINI3": "ICD-10 of the 3rd previous treatment, or empty.",
    "AR_DTINI3": "Start date of the 3rd previous treatment (YYYYMMDD), or empty/zeros.",
    "AR_CONTTR": "Continuation of a treatment already under way: S = yes, N = no (mostly N).",
    "AR_DTINTR": "Start date of the requested treatment (YYYYMMDD).",
    "AR_FINALI": "Purpose of the radiotherapy: 1 = radical (curative), 2 = adjuvant, 3 = pain relief "
                 "(antiálgica), 4 = palliative, 5 = prior (neoadjuvant), 6 = to stop bleeding "
                 "(anti-hemorrágica). 7 (and before 2019 also 8, 9, 0) occur and are not in the layout.",
    "AR_CIDTR1": "Topography of the 1st area treated (irradiated), ICD-10. Usually AP_CIDPRI; for metastases "
                 "the site irradiated (C795 bone, C793 brain). Joins cid10.",
    "AR_CIDTR2": "Topography of the 2nd area treated, ICD-10, or empty. Always empty since 2020.",
    "AR_CIDTR3": "Topography of the 3rd area treated, ICD-10, or empty. Always empty since 2020.",
    "AR_NUMC1": "Number of fields or insertions for the 1st area (3 digits, also '4', '04'); some facilities "
                "write the total field applications planned (e.g. 120 = 4 fields x 30 sessions). Always "
                "empty since 2020.",
    "AR_INIAR1": "Start date of the irradiation of the 1st area (YYYYMMDD).",
    "AR_INIAR2": "Start date of the irradiation of the 2nd area (YYYYMMDD), or empty/zeros.",
    "AR_INIAR3": "Start date of the irradiation of the 3rd area (YYYYMMDD), or empty/zeros.",
    "AR_FIMAR1": "End date of the irradiation of the 1st area (YYYYMMDD).",
    "AR_FIMAR2": "End date of the irradiation of the 2nd area (YYYYMMDD), or empty/zeros.",
    "AR_FIMAR3": "End date of the irradiation of the 3rd area (YYYYMMDD), or empty/zeros.",
    "AR_NUMC2": "Number of fields or insertions for the 2nd area, or empty/'000'. Always empty since 2020.",
    "AR_NUMC3": "Number of fields or insertions for the 3rd area, or empty/'000'. Always empty since 2020.",
})


# ------------------------------------------------------------------- AD
# APAC de Laudos Diversos, files AD<UF><YY><MM>.dbc, Jan/2008 onward: the APACs of every
# procedure that has no laudo of its own (eye surgery and injections, hearing diagnosis and
# aids, cardiac catheterisation, transplant follow-up, PET-CT, wheelchairs, ...). Only the
# shared AP_ columns, no AD_ column. One layout: AP_NATJUR added Jul/2016 (NULL before).
# Source: "Informe Técnico SIASUS" (Jul/2019), section 3.4.1 "Layout do arquivo de laudos
# diversos: ADUFAAMM.DBF" (URL above). Procedure mix by year: docs/tables/ad.md.
AD_QUANTITY_COLS = APAC_QUANTITY_COLS
AD_VALUE_COLS = APAC_VALUE_COLS

AD = apac("AD", {
    "AP_PRIPAL": "Main procedure of the APAC, SIGTAP code (10 digits), from many groups: the procedure's "
                 "grupo/subgrupo in procedimentos says what kind of care the row is (0405 eye surgery, "
                 "0211 diagnosis in specialties, 0506 transplant follow-up, 0301 consultations/follow-up, "
                 "0701 orthoses/prostheses, ...). Until Dec/2012 mostly CAPS mental health follow-up "
                 "(030108, moved to RAAS). NULL on 23,613 rows, mostly Jan-Mar/2013 and Sep-Nov/2023: "
                 "APACs billed late with a code just retired (pa has the code). Joins procedimentos; "
                 "fetch past SIGTAP versions for old codes.",
    "AP_VL_AP": "Approved value of the APAC in this month, R$ (number, nominal) = SUM(PA_VALAPR) of its pa "
                "rows (main + secondary procedures). 0 on about 7% of rows since 2023 (31% of transplant "
                "follow-up rows).",
    "AP_TPATEN": "APAC type of care; always 00 in AD (no specific laudo).",
    "AP_TPAPAC": "1 = initial, 2 = continuation, 3 = single. Depends on the procedure: surgery, exams and "
                 "devices are single APACs (3); follow-up (transplant, retina treatment, CAPS until 2012, "
                 "...) runs 1 then 2. 4 (not in the layout) on 760 rows, all without a procedure.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AD (362 exceptions "
                "in 61 M rows; wrong): compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS. Empty (NULL) or the placeholder '{{{{{{{{{{{{{{{' on a "
                 "share of rows that grows from Apr/2024 (13% in Jan/2025, 35% in Jan/2026, 67% in Aug/2026): "
                 "exclude both before counting or following patients.",
    "AP_CIDPRI": "Main diagnosis, ICD-10 (no dot): eye (H25/H26 cataract, H35/H36 retina, H40 glaucoma), "
                 "hearing loss (H90/H91), transplanted organ (Z94x), angina (I20), mental disorders (F, "
                 "until 2012), ... Joins cid10.",
})


# ------------------------------------------------------------------- ATD
# APAC de Tratamento Dialítico (chronic dialysis: haemodialysis and peritoneal dialysis), files
# ATD<UF><YY><MM>.dbc, Aug/2014 onward; replaces AN (APAC Nefrologia, until Jul/2014). One layout:
# the 45 shared AP_ columns, 19 ATD_ columns, then AP_NATJUR (appended last, from Jul/2016).
# Sources: "Informe Técnico SIASUS" (Jul/2019), section 3.4.8 "Layout do arquivo de APAC de
# tratamento dialítico: ATDUFMM.DBF" (URL above), for the columns; DATASUS "Layout da interface
# texto do APAC e do SIA - layout interno" (Apr/2014), "parte variável 18 - laudo de Tratamento
# Dialítico", for the code lists. Value checks, lab value formats and the AN -> ATD transition:
# docs/tables/atd.md.
ATD_QUANTITY_COLS = APAC_QUANTITY_COLS
ATD_VALUE_COLS = APAC_VALUE_COLS

_LAB = ("Free text, 4 characters (the layout says 'number, decimal point allowed'): '12.3' and '12,3' "
        "are decimals, '0000' (or 0) = not measured, bare digits ('0010', '11') are ambiguous, and "
        "'9999', 'N', '70%' also occur. Parse with TRY_CAST(REPLACE(x, ',', '.') AS DOUBLE) and keep a "
        "plausible range: see docs/tables/atd.md.")

ATD = apac("ATD", {
    "AP_PRIPAL": "Dialysis procedure, SIGTAP 0305010xxx: 0305010107 haemodialysis (max. 3 sessions/week, ~91% "
                 "of rows), 0305010115 haemodialysis in a patient with positive HIV/HBV/HCV serology, "
                 "0305010166 home peritoneal dialysis follow-up (CAPD/APD, one per month), 0305010182 PD "
                 "training, 0305010204 paediatric haemodialysis, 0305010026 intermittent PD. NULL on 90 rows "
                 "(all with AP_TPAPAC = 4). Joins procedimentos.",
    "AP_VL_AP": "Approved value of the APAC in this month, R$ (number, nominal) = SUM(PA_VALAPR) of its pa rows: "
                "the sessions (the P row; PA_QTDAPR = number of sessions) plus secondary procedures (lab "
                "tests, catheters, materials). Median ~R$ 3,300 a month for haemodialysis in 2026.",
    "AP_TPATEN": "APAC type of care; always 10 (dialysis) in ATD.",
    "AP_TPAPAC": "1 = initial, 2 = continuation, 3 = single (PD training only). Dialysis APACs run three "
                 "months: about 35% of rows are 1 and 64% are 2 every year. 4 (not in the layout) on 90 rows, "
                 "all without a procedure.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in ATD (wrong, as in the "
                "other APAC types): compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS (same encoding as AN and the other APAC types). Empty (NULL) "
                 "or the placeholder '{{{{{{{{{{{{{{{' on 0% of rows until Mar/2024, ~2% until Oct/2024, 7-15% "
                 "until Mar/2026, then 46% (May/2026), 66% (Jun), 90% (Jul) and 96% (Aug/2026): exclude both "
                 "before counting or following patients.",
    "AP_CIDPRI": "Main diagnosis: always '0000' in ATD (not filled). Use pa (PA_CIDPRI) for a diagnosis.",
    "AP_CIDSEC": "Secondary diagnosis: always '0000' in ATD (not filled).",
    "AP_CIDCAS": "Associated cause, ICD-10 (no dot), or '0000' (88% of rows since 2024; 76% in 2014). The only "
                 "diagnosis ATD carries: N180/N188/N189 chronic kidney disease, and for 0305010115 the infection "
                 "behind the positive serology (B182/B181 chronic hepatitis C/B, Z21/B24 HIV). Joins cid10.",
    "ATD_CARACT": "Characteristic of the treatment: 1 = new case, 2 = continuing treatment, 3 = patient in "
                  "transit (dialysing away from home), 4 = transfer from another facility. Not reliable as "
                  "'incident patient': on '1' rows dialysis started a median of 8 months before (use ATD_DTPDR).",
    "ATD_DTPDR": "Date the patient started dialysis for the first time, anywhere (YYYYMMDD). Filled except "
                 "on the 90 rows without a procedure; a few impossible dates (e.g. 9999xxxx).",
    "ATD_DTCLI": "Date the patient started dialysis at this facility (YYYYMMDD).",
    "ATD_ACEVAS": "Vascular (dialysis) access: 1 = arteriovenous fistula (FAV), 2 = short-term catheter, "
                  "3 = long-term catheter. Filled on every row, also for peritoneal dialysis (where 3 "
                  "normally means the Tenckhoff catheter).",
    "ATD_MAISNE": "Followed by a nephrologist for more than a year before starting dialysis: S = yes, N = no, "
                  "I = unknown. Only required for new cases (ATD_CARACT = 1); often empty otherwise.",
    "ATD_SITINI": "Patient's situation when dialysis started: A = outpatient, H = in hospital, I = unknown. "
                  "Only required for new cases (ATD_CARACT = 1).",
    "ATD_SITTRA": "Transplant situation: 1 = fit for a kidney transplant, 2 = unfit, 3 = refuses, 4 = not "
                  "applicable (new case, less than 90 days of dialysis).",
    "ATD_SEAPTO": "If fit for transplant (ATD_SITTRA = 1): 1 = on the waiting list (CNCDO), 2 = being "
                  "assessed at a transplant centre, 3 = not referred, 4 = awaiting an appointment at the "
                  "transplant centre. Empty or 0 when ATD_SITTRA is not 1 (with exceptions).",
    "ATD_HB": "Haemoglobin, g/dL (median 10.6 in 2024-2026). " + _LAB,
    "ATD_FOSFOR": "Serum phosphorus, mg/dL (median 4.9). " + _LAB,
    "ATD_KTVSEM": "Kt/V (dialysis adequacy, no unit; median 1.39, which looks like a per-session value "
                  "although the layout says weekly). Optional; mostly empty for peritoneal dialysis. " + _LAB,
    "ATD_TRU": "Urea reduction ratio (URR), % (median 69). Optional; mostly empty for peritoneal dialysis. " + _LAB,
    "ATD_ALBUMI": "Serum albumin, g/dL (median 3.9). Optional. " + _LAB,
    "ATD_PTH": "Parathyroid hormone (PTH), pg/mL (median ~170-310; mostly written as a 4-digit integer, "
               "'0624'). Optional. " + _LAB,
    "ATD_HIV": "Anti-HIV antibodies: P = positive, N = negative (optional, may be empty).",
    "ATD_HCV": "Anti-HCV antibodies (hepatitis C): P = positive, N = negative (optional, may be empty).",
    "ATD_HBSAG": "HBsAg (hepatitis B surface antigen): P = positive, N = negative (optional, may be empty).",
    "ATD_INTERC": "Patient was admitted to hospital, starting this month, to treat a clinical complication: "
                  "S = yes, N = no, I = unknown.",
    "ATD_SEPERI": "If on peritoneal dialysis, peritonitis was diagnosed this month: S = yes, N = no, "
                  "I = unknown. Filled on haemodialysis rows too (ignore it there).",
})


# ------------------------------------------------------------------- AN
# APAC de Nefrologia (chronic dialysis), files AN<UF><YY><MM>.dbc, Jan/2008 to Oct/2014; replaced
# by ATD from Aug/2014 (AN's last real month is Jul/2014; Aug-Oct/2014 hold 280 late bills). One
# layout: the 45 shared AP_ columns and 15 AN_ columns (60); the Dec/2011 files of every state
# also carry AP_NATJUR, appended last (61), as do the other APAC types and BI that month.
# Sources: "Informe Técnico SIASUS" (Jul/2019), section 3.4.3 "Layout do arquivo de APAC de
# nefrologia: ANUFMM.DBF" (URL above), for the columns; DATASUS "Layout da interface texto do
# APAC e do SIA - layout interno" (Apr/2014), "parte variável 09 - Nefrologia", for the codes
# and for which fields are filled on the first dialysis (*), on later months (**) or both (***).
# Value checks and the AN -> ATD transition: docs/tables/an.md and docs/tables/atd.md.
AN_QUANTITY_COLS = APAC_QUANTITY_COLS
AN_VALUE_COLS = APAC_VALUE_COLS

_AN_FIRST = (" Layout: first dialysis only (*); in the files, filled on every AP_TPAPAC = 1 row and on 77% of "
             "continuation rows (NULL on the others).")
_AN_FOLLOW = (" Layout: later months only (**); in the files, filled on every AP_TPAPAC = 2 row and on 44% of "
              "AP_TPAPAC = 1 rows (NULL on the others).")
_AN_TEXT = (" Text, as typed by the facility: zero ('0', '00', ...) = not measured; a few typos ('9,', 'NN', '##'). "
            "See docs/tables/an.md.")

AN = apac("AN", {
    "_ARQUIVO_ORIGEM": "Original DATASUS file this row came from (e.g. ANSP1405.dbc).",
    "AP_PRIPAL": "Dialysis procedure, SIGTAP 0305010xxx: 0305010107 haemodialysis (max. 3 sessions/week, 91.5% of "
                 "rows), 0305010166 home peritoneal dialysis follow-up (CAPD/APD, 7.2%), 0305010115 haemodialysis "
                 "with positive HIV/HBV/HCV serology, 0305010182 PD training, 0305010026 intermittent PD, "
                 "0305010069 / 0305010085 'hemodiálise I' (plain / HIV; retired codes, until Sep/2012), 0305010204 "
                 "paediatric haemodialysis (2014 only). Never NULL. Joins procedimentos.",
    "AP_VL_AP": "Approved value of the APAC in this month, R$ (number, nominal) = SUM(PA_VALAPR) of its pa rows: "
                "the sessions (the P row) plus secondary procedures (lab tests, materials). Median ~R$ 2,390 a "
                "month for haemodialysis in May/2014.",
    "AP_TPATEN": "APAC type of care; always 02 in AN (ATD uses 10).",
    "AP_TPAPAC": "1 = initial, 2 = continuation, 3 = single (mostly PD training). Dialysis APACs run three months: "
                 "about 36% of rows are 1 and 64% are 2 every year.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AN (wrong, as in the other "
                "APAC types): compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS (same encoding as ATD and the other APAC types). Filled on "
                 "every row except 58 (2008-2012). Same patient in ATD from Aug/2014.",
    "AP_CIDPRI": "Main diagnosis, ICD-10 (no dot). Always filled in AN (unlike ATD): N180 (end-stage kidney "
                 "disease) on 98% of rows, then N189, I120, N039, N083, I10. Joins cid10.",
    "AP_CIDSEC": "Secondary diagnosis, ICD-10 (no dot), or '0000' (13% of rows): mostly the underlying cause, "
                 "N189 (34%), N180, I10 hypertension, N188, I120 hypertensive kidney disease, E142 diabetes. "
                 "Joins cid10.",
    "AP_CIDCAS": "Associated cause, ICD-10, or '0000' (76% of rows); otherwise mostly N180. Joins cid10.",
    "AP_NATJUR": "Facility legal nature. Only in the Dec/2011 files, and empty (NULL) on every row there; NULL "
                 "in every other month (AN ended before Jul/2016, when the other APAC types got the column).",
    "AN_DTPDR": "Date of the patient's first dialysis ever (YYYYMMDD)." + _AN_FIRST,
    "AN_ALTURA": "Patient height, cm (3 digits, e.g. '165'; '000'/'0' on ~21% of rows = not informed)." + _AN_FIRST,
    "AN_PESO": "Patient weight, kg (3 digits, e.g. '065' or '65'; zero on ~20% = not informed)." + _AN_FIRST,
    "AN_DIURES": "Residual diuresis (urine output), mL/24 h (4 digits; zero on about half the rows: anuric or not "
                 "informed)." + _AN_FIRST,
    "AN_GLICOS": "Blood glucose, mg/dL (4 digits; zero on ~30% of rows = not informed)." + _AN_FIRST,
    "AN_ACEVAS": "Has a vascular access (S = yes, N = no). Not the access type (ATD_ACEVAS has the type); a few "
                 "rows carry digits, e.g. '2' in 2014." + _AN_FIRST,
    "AN_ULSOAB": "Abdominal ultrasound done (S = yes, N = no)." + _AN_FIRST,
    "AN_TRU": "Urea reduction ratio (URR), % (4 characters; integer on almost every row, e.g. '69' or '0070'; "
              "decimal comma on ~1% in 2014; zero on ~30% = not measured)." + _AN_FOLLOW + _AN_TEXT,
    "AN_INTFIS": "Number of interventions on the arteriovenous fistula (2 digits; mostly 0 or 1). Filled like "
                 "AN_TRU, but NULL on 24% of continuation rows too." + _AN_FOLLOW,
    "AN_CNCDO": "Registered on the transplant waiting list (CNCDO): S = yes, N = no. S fell from 39% of rows "
                "(2008) to 28% (2014)." + _AN_FOLLOW,
    "AN_ALBUMI": "Serum albumin, g% (= g/dL), 2 characters, every month (***). About 53% of rows are one "
                 "non-zero digit (g/dL, rounded: '4', '04'), ~20% are tenths without the point ('39' = 3.9 g/dL: "
                 "read 10-60 as x/10) and 25% zero."
                 + _AN_TEXT,
    "AN_HCV": "Anti-HCV antibodies (hepatitis C): P = positive (5.6% of rows in 2008, 3.0% in 2014), "
              "N = negative. Always filled (***).",
    "AN_HBSAG": "HBsAg (hepatitis B surface antigen): P = positive (~1%), N = negative. Always filled (***).",
    "AN_HIV": "Anti-HIV antibodies: P = positive (~0.7%), N = negative. Always filled (***).",
    "AN_HB": "Haemoglobin, g% (= g/dL), 2 characters, whole number ('11', '09'), every month (***). Plausible "
             "(3-20) on 74% of rows; zero on 18%; 21-99 on 7% (e.g. '93', '99': 9.3 without the point, or "
             "filler)." + _AN_TEXT,
})


# ------------------------------------------------------------------- RAAS (shared)
# Columns shared by the RAAS file types (PS, SAD): Registro das Ações Ambulatoriais de Saúde.
# No AP_ prefix and no authorisation number. A RAAS is one care episode (facility + patient +
# start date) re-recorded every month with the actions done that month; the files hold one row
# per action line, with the episode's fields repeated. Same names and meaning in both layouts.
# Sources: DATASUS, "Informe Técnico SIASUS" (Jul/2019), section 4 "Registro das Ações
# Ambulatoriais de Saúde - RAAS" (4.1 SAD, 4.2 PS), URL above, for the columns; Ministério da
# Saúde, "Manual Operacional RAAS" v1.5 (RAAS 01.40), for how a RAAS is recorded. The Informe
# names some PS columns differently from the files (QT_APRES / QT_APROV, SERV, CLASS); the names
# below are those in the files. Values described here were checked on the whole PS history; SAD
# may differ: give it its own overrides in raas("SAD", {...}).
# What RAAS is and how it reaches pa (PA_DOCORIG = 'A' / 'B'): docs/tables/raas.md.
RAAS_QUANTITY_COLS = ("PA_QTDPRO", "PA_QTDAPR")
RAAS_VALUE_COLS: tuple[str, ...] = ()  # RAAS files carry no value column (pa has R$ 0 for these rows)

RAAS_COMMON = {
    "CNES_EXEC": "Facility code (CNES, 7 digits) that delivered the care. Same as PA_CODUNI.",
    "GESTAO": "Managing authority: UF code + IBGE municipality code of the manager, or UF + '0000' "
              "when the facility is under state management.",
    "CONDIC": "Type of management the state/municipality is qualified for (values seen: PG, EP, MN).",
    "UFMUN": "Municipality of the FACILITY (IBGE, 6 digits). First 2 digits = state. Same as PA_UFMUN.",
    "TPUPS": "Facility type, CNES codes (70 = CAPS, 36 = specialised clinic, 07 = specialised hospital, ...).",
    "MN_IND": "Facility is maintained by a body (M) or independent (I; 'U' in the files).",
    "CNPJCPF": "Facility tax ID (CNPJ).",
    "CNPJMNT": "Maintaining body's CNPJ, or zeros if none.",
    "DT_PROCESS": "Processing month (YYYYMM). Equals competencia. Same as PA_MVM.",
    "DT_ATEND": "Month the care was delivered (competência, YYYYMM). Earlier than DT_PROCESS on late "
                "reports. Same as PA_CMP.",
    "CNS_PAC": "Patient's national health card (CNS), ENCODED by DATASUS (not the real number), with the same "
               "encoding as the APAC files' AP_CNSPCN. Same value = same patient within the data; cannot be "
               "linked to other systems. '{{{{{{{{{{{{{{{' = encoded blank (no CNS).",
    "DTNASC": "Patient's date of birth (YYYYMMDD).",
    "TPIDADEPAC": "Unit of IDADEPAC, computed from the date of birth: 2 = days, 3 = months, 4 = years, "
                  "5 = 100 years or more (age = 100 + IDADEPAC), 9 = not informed.",
    "IDADEPAC": "Patient age (2 characters), in the unit given by TPIDADEPAC.",
    "NACION_PAC": "Patient nationality (2 characters; 01 = Brazilian).",
    "SEXOPAC": "Patient sex (M, F).",
    "RACACOR": "Race/colour (01 white, 02 black, 03 brown, 04 yellow, 05 indigenous, 99 not informed).",
    "ETNIA": "Indigenous ethnicity code (Portaria SAS 508/2010, annex I); only when RACACOR = 05.",
    "MUNPAC": "Municipality where the PATIENT lives (IBGE, 6 digits).",
    "MOT_COB": "Reason for exit or continuation (motivo de saída/permanência), APAC codes: 21 = continues "
               "(nature of the disease), 28 = continues (other reasons), 11 = discharge cured, 12 = improved, "
               "15 = discharge with follow-up elsewhere, 18 = other discharge (e.g. abandonment), 31 = transfer, "
               "4x = death.",
    "DT_MOTCOB": "Date of the discharge, transfer or death (YYYYMMDD); usually NULL even then (use DT_FIM).",
    "CATEND": "Type of care (caráter de atendimento): 01 = elective, 02 = urgent, 03-06 = work/traffic "
              "accident and other external causes.",
    "CIDPRI": "Main diagnosis of the episode, ICD-10 (no dot, 3 or 4 characters). Joins cid10.",
    "CIDASSOC": "Associated cause, ICD-10 (no dot), or NULL. Joins cid10.",
    "ORIGEM_PAC": "Where the patient came from (origem do usuário), set in the first month of the episode and "
                  "copied forward; codes 01-06 (the code list is not in the Informe).",
    "DT_INICIO": "Start date of the episode (admission) at this facility (YYYYMMDD). With CNES_EXEC, CNS_PAC "
                 "and DT_ATEND it identifies the RAAS (episode-month).",
    "DT_FIM": "End date of the episode (YYYYMMDD); NULL while the patient stays in care (DESTINOPAC = '00').",
    "COB_ESF": "Patient's area is covered by the Family Health Strategy (ESF): S = yes, N = no.",
    "CNES_ESF": "CNES of the Family Health unit of the patient's area (when COB_ESF = 'S').",
    "DESTINOPAC": "Destination of the patient (destino do usuário): 00 = stays in care (permanência; the RAAS "
                  "continues next month); any other code closes the episode and comes with DT_FIM (code list "
                  "not in the Informe).",
    "PA_PROC_ID": "Procedure (ação realizada), SIGTAP code (10 digits). Same as PA_PROC_ID. Joins procedimentos.",
    "PA_QTDPRO": "Quantity submitted (number). Same as PA_QTDPRO.",
    "PA_QTDAPR": "Quantity approved (number). Sum this, don't count rows. Same as PA_QTDAPR.",
    "PA_SRV": "Specialised service code (CNES service, 3 digits). Same as the first part of PA_SRV_C.",
    "PA_CLASS_S": "Service classification code (3 digits). Same as the second part of PA_SRV_C.",
    "INICIO": "First day in care in this month (YYYYMMDD; the Informe says DDMMAAAA, wrong). Filled on one "
              "row per episode-month only (the row with QTDPCN = '1'); NULL on the others.",
    "FIM": "Last day in care in this month (YYYYMMDD). Filled like INICIO.",
    "PERMANEN": "Days in care in this month = FIM - INICIO + 1 (text, 1-31). Filled like INICIO.",
    "QTDATE": "'1' on one row per episode-month (the episode's summary line), '0' on the other rows.",
    "QTDPCN": "'1' on one row per episode-month, '0' on the others: SUM(QTDPCN::INT) = number of patient-"
              "months (RAAS). Same rows as QTDATE = '1'.",
    "NAT_JUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table: 1244 = municipality, "
               "1031 = municipal executive body, ...). From Jul/2016; NULL before.",
}


def raas(code: str, own: dict[str, str], without: tuple[str, ...] = ()) -> dict[str, str]:
    """Dictionary of a RAAS file type: partition columns, the shared RAAS columns (minus
    ``without``) and the type's own columns (``own``, which may also override shared ones)."""
    return {
        **PARTITION,
        "competencia": "Partition: month of the file (YYYYMM). Equals DT_PROCESS (processing month).",
        "uf": "Partition: state of the file (SP, RJ, ...). Same as the facility's state.",
        "_ARQUIVO_ORIGEM": f"Original DATASUS file this row came from (e.g. {code}SP2605.dbc).",
        **{k: v for k, v in RAAS_COMMON.items() if k not in without},
        **own,
    }


# ------------------------------------------------------------------- PS
# RAAS Psicossocial (Atenção Psicossocial: CAPS), files PS<UF><YY><MM>.dbc, Nov/2012 onward (the
# CAPS care billed on APAC in AD until Dec/2012). One layout: the RAAS columns plus TIPPRE, SIT_RUA,
# TP_DROGA, LOC_REALIZ (44); NAT_JUR (45th, last) in the Oct/2014 files and from Jul/2016 (every
# month of SP probed). Source: "Informe Técnico SIASUS" (Jul/2019), section 4.2 "Layout do arquivo
# de RAAS - Psicossocial: PS*.DBF" (URL above). PS rows are the pa rows with PA_DOCORIG = 'B'
# (same rows and quantities, R$ 0): never sum ps and pa together. Details: docs/tables/ps.md.
PS_QUANTITY_COLS = RAAS_QUANTITY_COLS
PS_VALUE_COLS = RAAS_VALUE_COLS

PS = raas("PS", {
    "TPUPS": "Facility type, CNES codes: 70 = CAPS on 99.3% of rows; 36 = specialised clinic, "
             "07 = specialised hospital.",
    "TIPPRE": "Provider type: real codes until Dec/2013 (50 on 92% of rows, 61, 40, 60, 20, 30), then '00' "
              "on more and more rows, and only '00' from Nov/2015. (The DBF field name is space-padded, "
              "'TIPPRE  '; the converter strips it.)",
    "PA_PROC_ID": "Action (ação realizada), SIGTAP 030108xxxx, CAPS care: 0301080208 individual care (43% of "
                  "rows), 0301080216 group care, 0301080194 day-time stay (acolhimento diurno), 0301080224 "
                  "family care, 0301080283 expressive practices, 0301080348 psychosocial rehabilitation, "
                  "0301080275 body practices, 0301080291 crisis care, 0301080240 home visit, 0301080356 "
                  "contractuality in the community, 0301080020 night stay, 0301080046 therapeutic residence, "
                  "0301080038 third-shift stay. Joins procedimentos.",
    "PA_QTDAPR": "Quantity approved (number). Sum this, don't count rows. 0 on 5-11% of rows (rejected). "
                 "Same as PA_QTDAPR.",
    "PA_SRV": "Specialised service: always 115 (psychosocial care).",
    "PA_CLASS_S": "Service classification (with PA_SRV = 115): 002 on 99.5% of rows; also 001, 004, 005.",
    "CIDPRI": "Main diagnosis of the episode, ICD-10 (no dot, 3 or 4 characters: both 'F20' and 'F200' "
              "occur). Almost always chapter F: F99, F20/F200 schizophrenia, F102/F192 alcohol / multiple "
              "drug dependence, F29, F32, F31. Joins cid10 (which has both 3- and 4-character codes).",
    "ORIGEM_PAC": "Where the patient came from (origem do usuário), set in the first month and copied forward: "
                  "01 (51% of rows; presumably spontaneous demand), 02 (37%; presumably primary care), 03-06 "
                  "(2-3% each). The code list is not in the Informe.",
    "SIT_RUA": "Patient lives on the street (S = yes, 2.4% of rows; N = no). Asked again every month.",
    "TP_DROGA": "Drugs used, letters combined: A = alcohol, C = crack, O = other ('AO', 'ACO', ...; a few "
                "'N', 'NNN', spaces). NULL = no drug use informed (77% of rows: 98% in 2013, 72-82% each "
                "year since 2014).",
    "LOC_REALIZ": "Where the action took place: C = at the CAPS (98%), T = in the community (território). "
                  "Home visits (0301080240) are T on 36% of rows.",
    "NAT_JUR": "Facility legal nature (IBGE CONCLA code: 1244 = municipality 67% of rows, 1031 = municipal "
               "executive body 13%, 1023 = state / Federal District executive body, 3999 = private association, ...). From Jul/2016; NULL before, except in the "
               "Oct/2014 files (the column was there that month only).",
})


# ------------------------------------------------------------------- SAD
# RAAS Atenção Domiciliar (home care by Melhor em Casa teams: EMAD, EMAP), files
# SAD<UF><YY><MM>.dbc, Apr/2012 to Oct/2018 (discontinued; in practice the teams stopped using
# RAAS-AD between Aug/2015 and Jun/2016, when their records moved to e-SUS AD / SISAB, Portaria
# GM/MS 1.653/2015). One layout with three column sets (every one of the 1,088 files probed): the
# RAAS columns plus PA_EQUIPE, PA_TP_EQP, PA_CID (43) until Dec/2014; CO_INE added (44) from
# Jan/2015; NAT_JUR after it (45) in the Oct/2014 files and from Jul/2016. Source: "Informe Técnico
# SIASUS" (Jul/2019), section 4.1 "Layout do arquivo de Atenção Domiciliar: SAD*.DBF" (URL above;
# it lists neither CO_INE nor NAT_JUR, and calls PA_CLASS_S "PA_CLAS_S" and DESTINOPAC
# "DESTINO_PAC"). SAD rows are the pa rows with PA_DOCORIG = 'A' (R$ 0): never sum sad and pa
# together. Values below were checked on the whole history (3.52 M rows). Details: docs/tables/sad.md.
SAD_QUANTITY_COLS = RAAS_QUANTITY_COLS
SAD_VALUE_COLS = RAAS_VALUE_COLS

SAD = raas("SAD", {
    "TPUPS": "In SAD this holds the PROVIDER TYPE (tipo de prestador, = pa's PA_TIPPRE), not the facility "
             "type: 50 (77% of rows), 00 (12%), 40 (8%), 30, 61. The facility type is in pa (PA_TPUPS: "
             "02 = health centre, 05 = general hospital, ...).",
    "MOT_COB": "Reason for exit or continuation (motivo de saída/permanência), APAC codes: 21 = continues "
               "(88% of rows), 28 = continues (other reasons), 11 = discharge cured, 12 = improved, 18 = other "
               "discharge, 31 = transfer, 41 = death (1.7%), 51 = closed administratively (0.9%; almost always with "
               "DESTINOPAC = '00').",
    "CIDPRI": "Main diagnosis of the episode, ICD-10 (no dot, 3 or 4 characters). NULL on 10% of rows (13% of "
              "patient-months). Mostly stroke and its sequelae (I694, I64, I69), hypertension (I10), pressure "
              "ulcers (L89), Alzheimer's (G30), COPD (J44), femur fracture (S72). Joins cid10.",
    "ORIGEM_PAC": "Where the patient came from (origem do usuário), set in the first month and copied forward: "
                  "02 (55% of rows), 03 (23%), 05 (15%), 01 (6%), 04 (0.7%). The code list is not in the "
                  "Informe nor in Portaria SAS 276/2012.",
    "DESTINOPAC": "Destination of the patient (destino do usuário): 00 = stays in care (89% of rows); the "
                  "others close the episode and pair with MOT_COB: 01 with 11 (discharge cured), 02 with 12 "
                  "(improved), 03 with 18 (other discharge), 04 and 05 with 31 (transfer), 06 with 41 (death). "
                  "Code names are not in the Informe.",
    "PA_PROC_ID": "Action (ação realizada), SIGTAP code. 69 codes; most rows: 0301010137 home consultation "
                  "(19%), 0301050023 home care by a multiprofessional team (13%), 0301050058 home care by a "
                  "mid-level professional (13%), 0101030010 / 0301050147 / 0101030029 home visits, 0401010023 "
                  "and 0401010015 wound dressing (grade I, retired after May/2015; grade II), 0214010015 capillary glucose, physiotherapy (0302...), "
                  "0301050082 parenteral antibiotics, 0301100144 oxygen therapy. Joins procedimentos.",
    "PA_QTDAPR": "Quantity approved (number). Sum this, don't count rows. Equal to PA_QTDPRO on all but 19 "
                 "rows; 0 on 0.7% (and on every row of PI from 2017). Same as PA_QTDAPR.",
    "PA_SRV": "Specialised service: 113 (home care, atenção domiciliar) on all but 9 rows (126).",
    "PA_CLASS_S": "Service classification (with PA_SRV = 113): 003 on 93% of rows, 004 on 7% (mostly EMAP "
                  "rows), a few 001 / 000. (The Informe calls the column PA_CLAS_S.)",
    "INICIO": "First day in care in this month (YYYYMMDD; the Informe says DDMMAAAA, wrong). Filled on the one "
              "row per episode-month with QTDPCN = '1' (13.6% of rows); NULL on the others.",
    "QTDATE": "'1' on one row per episode-month (the episode's summary line), '0' on the other rows. Same as "
              "QTDPCN except on 951 rows.",
    "QTDPCN": "'1' on one row per episode-month, '0' on the others: SUM(QTDPCN::INT) = number of patient-"
              "months (RAAS). 0.2% of episode-months have no such row; none has two.",
    "PA_EQUIPE": "Home-care team code (código da equipe, 12 digits, CNES; the Informe: 'only for the RAAS "
                 "instrument'). Filled on every row until Jul/2015, then replaced by CO_INE: NULL on 69% of "
                 "rows in Aug/2015, on 92-100% from Sep/2015.",
    "PA_TP_EQP": "Home-care team type (CNES team type): 22 = EMAD (multiprofessional home-care team; 56% of "
                 "rows), 23 = EMAP (multiprofessional support team; 10%), 46 = EMAD type II (from 2013, 2%). "
                 "NULL on 32% of rows: 2-52% a month in 2012, 9-36% in 2013, 8-18% from 2014 to Jul/2015, then on "
                 "almost all (like PA_EQUIPE).",
    "PA_CID": "ICD-10 of the action (CID do procedimento), no dot. Filled on 39% of rows (the procedures that "
              "require one); differs from CIDPRI on 16% of those. Joins cid10.",
    "CO_INE": "Team identifier (INE, CNES national team code, 10 digits), the successor of PA_EQUIPE. Column "
              "from Jan/2015 (and in the Oct/2014 files, empty there); filled from Aug/2015 (on 80% of rows), on "
              "97-100% from Sep/2015. NULL before.",
    "NAT_JUR": "Facility legal nature (IBGE CONCLA code: 1031 = municipal executive body, 1201 = public fund "
               "(municipal health fund), 1023 = state executive body, 1244 = municipality, ...). Only in the Oct/2014 files "
               "(filled on every row) and from Jul/2016 (the 9,079 rows of Jul/2016-Oct/2018); NULL otherwise.",
})


# ------------------------------------------------------------------- AB
# APAC de Cirurgia Bariátrica: in fact the monthly FOLLOW-UP of patients after bariatric surgery
# (procedure 0301120056 on every row; the surgery itself is a hospital admission, in SIH). Files
# AB<UF><YY><MM>.dbc, Jan/2008 to Apr/2017, then again Jan-Jul/2025 (an exact copy of ABO for those
# months). From Jan/2014 every AB row is also in ABO, which has more states: see docs/tables/ab.md.
# One DBF layout: the 45 shared AP_ columns and 12 AB_ columns (57), plus AP_NATJUR last in the
# Dec/2011 files (empty there) and from Jul/2016 (58). Every one of the 635 headers was probed.
# The AB_ columns follow the OLD laudo (Portaria SAS 493/2007, until Mar/2013). From care month
# Apr/2013 facilities fill the NEW post-bariatric laudo, and DATASUS kept cutting the text at the
# old field positions, so the same columns hold other fields: each description gives both readings.
# Sources: "Informe Técnico SIASUS" (Jul/2019), APAC section (URL above), for the columns;
# DATASUS "Layout da interface texto do APAC e do SIA - layout interno" (Apr/2014), "parte
# variável - Procedimentos de Cirurgia Bariátrica" (until Mar/2013) and "... Acompanh. PÓS
# Cirurgia Bariátrica" (after Mar/2013), for the field positions and codes.
AB_QUANTITY_COLS = APAC_QUANTITY_COLS
AB_VALUE_COLS = APAC_VALUE_COLS

_AB_OLD = " Until Mar/2013 (AB_PONTBAR '0'/'1'): "
_AB_NEW = " From Apr/2013 (AB_PONTBAR = 'E'): "

AB = apac("AB", {
    "_ARQUIVO_ORIGEM": "Original DATASUS file this row came from (e.g. ABSP1606.dbc).",
    "AP_PRIPAL": "Always 0301120056, follow-up of a patient after bariatric surgery by a multiprofessional "
                 "team (R$ 40 a month; R$ 39.38 until Mar/2013). NULL on one row (Jul/2025, AP_TPAPAC = 4). "
                 "Joins procedimentos.",
    "AP_VL_AP": "Approved value, R$ (nominal) = PA_VALAPR of the APAC's single pa row (no secondary "
                "procedures). 40.00 (39.38 until Mar/2013, 37.50 in 2008) or 0.00 (28% of rows, mostly continuation months).",
    "AP_TPATEN": "APAC type of care; always 05 in AB.",
    "AP_TPAPAC": "1 = initial, 2 = continuation, 3 = single (2008-2012 only), 4 = one row without a procedure "
                 "(Jul/2025). An APAC runs up to three months (median 87 days).",
    "AP_TIPPRE": "Provider type (same codes as pa's PA_TIPPRE): until 2017 61, 00, 40, 60, 30, 20, 22; "
                 "always 00 in 2025.",
    "AP_TPUPS": "Facility type, CNES codes: 05 = general hospital (98%), 07 = specialised hospital.",
    "AP_MNDIF": "Patient lives in another municipality than the facility. Always 1 in AB (wrong, as in the "
                "other APAC types): compare AP_MUNPCN with AP_UFMUN instead.",
    "AP_CNSPCN": "Patient's CNS, ENCODED by DATASUS (same encoding as the other APAC types). '{{{{{{{{{{{{{{{' "
                 "(placeholder) on 8% of rows in 2009, 2-4% in 2010-2011, none 2013-2017; empty or placeholder "
                 "on 17% of rows in 2025 (all of CE, 30% of SP, 25% of MG).",
    "AP_CIDPRI": "Always '0000' in AB: the diagnosis (E66x, obesity) is in AP_CIDCAS, or cut into "
                 "AB_PONTBAR/AB_TABBARR from Apr/2013.",
    "AP_CIDSEC": "Always '0000' in AB.",
    "AP_CIDCAS": "Associated cause, ICD-10, or '0000' (89% of rows); otherwise mostly E668/E660/E669 (obesity). "
                 "Joins cid10.",
    "AP_NATJUR": "Facility legal nature. In the Dec/2011 files (empty there) and from Jul/2016; NULL in "
                 "between.",
    "AB_IMC": "Patient's body mass index (BMI), kg/m2, whole number, 3 characters ('32' or '032'), same in both "
              "laudos. 0 on 8% of rows, NULL on 5%; 150-999 on 3% (BMI x 10 without the point, "
              "e.g. '345' = 34.5).",
    "AB_PROCAIH": "Text, 10 characters." + _AB_OLD + "SIGTAP code of the bariatric surgery (the AIH procedure): "
                  "0407010173 gastroplasty with intestinal bypass (93%), 0407010122 gastrectomy with or without "
                  "duodenal switch, 0407010181 vertical banded gastroplasty, plus typos." + _AB_NEW +
                  "3 chars % of excess weight lost, 3 chars kg lost, then 4 S/N flags for the surgery done: "
                  "gastrectomy with/without duodenal switch, sleeve gastrectomy, gastroplasty with intestinal "
                  "bypass, vertical banded gastroplasty (e.g. '30 30 NNSN' = 30%, 30 kg, bypass). Leading blanks "
                  "are stripped: lpad to 10 before cutting it.",
    "AB_DTCIRUR": "Date of the bariatric surgery (YYYYMMDD), same in both laudos. Filled on every row.",
    "AB_NUMAIH": "Number of the AIH (hospital admission, SIH) of the surgery, 13 digits, same in both laudos.",
    "AB_PRCAIH2": "Text, 10 characters." + _AB_OLD + "SIGTAP code of a second surgery (almost always empty)."
                  + _AB_NEW + "a blank, then S/N flags: any comorbidity, hypertension (I10), diabetes (O243 in "
                  "the layout), dyslipidaemia (E780), arthrosis (M199), sleep apnoea (G473), then the first 3 "
                  "characters of 'other comorbidity' (ICD-10). The leading blank is stripped: 'N' = no "
                  "comorbidity, 'SSNNNN' = comorbidity, hypertension only.",
    "AB_PRCAIH3": "Text, 10 characters." + _AB_OLD + "SIGTAP code of a third surgery (almost always empty)."
                  + _AB_NEW + "last character of 'other comorbidity' (usually blank, then stripped), then S/N: "
                  "uses medicines, physical activity, multivitamins, weight regain, healthy-diet adherence, "
                  "post-bariatric abdominal dermolipectomy (0413040054), then 3 digits: months after the "
                  "bariatric surgery it was done.",
    "AB_NUMAIH2": "Text, 13 characters." + _AB_OLD + "AIH number of a second surgery (almost always empty)."
                  + _AB_NEW + "plastic surgery after bariatric surgery, each as S/N + 3-digit months since the "
                  "bariatric surgery: mammoplasty (0413040089), brachial (0413040062) and crural (0413040070) "
                  "dermolipectomy, then the S/N of circumferential abdominal dermolipectomy (0414040267). "
                  "'N   N   N   N' = none.",
    "AB_DTCIRG2": "Text, 8 characters." + _AB_OLD + "date of a second surgery (YYYYMMDD; almost always empty)."
                  + _AB_NEW + "months since the bariatric surgery of the circumferential dermolipectomy "
                  "(3 digits; '000' or NULL).",
    "AB_MESACOM": "Number of months of follow-up (2 digits, '01' to '24' and more; also '1', '2', ...), both "
                  "laudos. NULL on 29% of rows.",
    "AB_ANOACOM": "Year of follow-up (4 characters, both laudos): mostly the calendar year ('2015') from 2013, "
                  "but also '0', '01'-'05' (year since surgery). NULL on half the rows.",
    "AB_PONTBAR": "Text, 1 character." + _AB_OLD + "BAROS score (Bariatric Analysis and Reporting Outcome "
                  "System, 'pontuação de Barros'), '0' or '1' (codes not documented)." + _AB_NEW +
                  "always 'E': the first character of the main diagnosis (E66x), which the new laudo has here. "
                  "Use it to tell the two readings apart.",
    "AB_TABBARR": "Text, 1 character." + _AB_OLD + "BAROS table (outcome class), '0' to '4' (codes not "
                  "documented)." + _AB_NEW + "always '6', the second character of the diagnosis (E66x).",
})
