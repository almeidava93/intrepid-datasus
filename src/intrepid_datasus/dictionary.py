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
