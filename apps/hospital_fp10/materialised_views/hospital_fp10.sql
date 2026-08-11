WITH bnf_chapter AS (
    SELECT DISTINCT name, code
    FROM bnf_code
    WHERE level = 1
)
SELECT
    date AS month,
    COALESCE(meds.name, rx.bnf_name) AS bnf_name,
    pres.bnf_code AS bnf_code,
    cd_cat.descr AS cd_category,                              -- gives CD status, with "no status" if it doesn't exist
    COALESCE(bnf_chapter.name, 'Unknown chapter') AS bnf_chapter, -- gives BNF chapter, with "unknown" if there's issue with drug (e.g. discontinued), mapped to the old code if the BNF map hasn't been updated
    HOSPITAL_TRUST_CODE AS hospital,
    SUM(TOTAL_QUANTITY) AS quantity,
    SUM(TOTAL_ITEMS) AS items,
    SUM(actual_cost) AS actual_cost

FROM hospital_prescribing AS rx

INNER JOIN presentation AS pres
    ON TRIM(rx.bnf_code) = COALESCE(pres.original_bnf_code, pres.bnf_code)

INNER JOIN bnf_chapter
    ON bnf_chapter.code = LEFT(COALESCE(pres.original_bnf_code, pres.bnf_code), 2)

INNER JOIN medications AS meds
    ON pres.snomed_code = meds.id

INNER JOIN control_info AS cd
    ON cd.vpid = meds.vmp_id

INNER JOIN control_drug_category AS cd_cat
    ON cd.catcd = cd_cat.cd
    
GROUP BY
    date,
    hospital,
    pres.bnf_code,
    COALESCE(meds.name, rx.bnf_name),
    bnf_chapter.name,
    cd_cat.descr