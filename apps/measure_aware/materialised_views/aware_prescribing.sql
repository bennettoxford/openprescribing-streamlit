WITH aware_vmps AS (
    SELECT DISTINCT
        vmp.vpid AS vmp_id,
        aware.aware_2024
    FROM vmp AS vmp
    INNER JOIN ont AS ont
        ON vmp.vpid = ont.vpid
    INNER JOIN ont_form_route AS ofr
        ON ont.formcd = ofr.cd
    INNER JOIN read_csv_auto('{data_dir}/tbl__aware_vtms.csv') AS aware
        ON vmp.vtmid = aware.vtm_id
    WHERE (
        aware.atc_route IS NULL
        OR (
            aware.atc_route = 'P'
            AND SPLIT_PART(ofr.descr, '.', 2)
                IN ('intravenous', 'intramuscular', 'intramuscular-deep')
        )
        OR (
            aware.atc_route = 'O'
            AND ofr.descr LIKE '%.oral'
        )
    )
    AND SPLIT_PART(ofr.descr, '.', 2)
        IN ('inhalation', 'intramuscular', 'intramuscular-deep', 'intravenous', 'oral', 'vaginal', 'gastroenteral', 'rectal')
    AND ofr.descr != 'gel.vaginal'
    AND ofr.descr != 'cream.vaginal'
)
SELECT date, practice_code, snomed_code, name, aware_2024, SUM(items) AS items
FROM aware_vmps
INNER JOIN medications
    ON aware_vmps.vmp_id = medications.vmp_id
INNER JOIN prescribing
    ON medications.id = prescribing.snomed_code
GROUP BY date, practice_code, snomed_code, name, aware_2024