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
    "NAT_JUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table). From Jul/2016; NULL before.",
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
                 "Can be empty or a placeholder in some types (AQ): see the table page.",
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
                "Unreliable (always 1 in AM and AQ): compare AP_MUNPCN with AP_UFMUN instead.",
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
    "AP_NATJUR": "Facility legal nature (natureza jurídica code, IBGE CONCLA table). From Jul/2016; NULL before.",
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
