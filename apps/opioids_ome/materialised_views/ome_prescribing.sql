SELECT 
    date, 
    practice_code, 
    snomed_code,
    COALESCE((SELECT nm FROM ing WHERE isid = vpi.bs_subid), ing.nm) as bs_name,
    name, 
    SUM(items) AS items, 
    SUM(quantity) AS quantity, 
    SUM(quantity * ome.weighting) AS total_ome
FROM prescribing AS rx
INNER JOIN medications
    ON medications.id = rx.snomed_code
INNER JOIN read_csv_auto('{data_dir}\ome_vmp.csv') AS ome
    ON ome.vmp_id = medications.vmp_id
INNER JOIN vpi
    ON medications.vmp_id = vpi.vpid
INNER JOIN ing
    ON vpi.isid = ing.isid
GROUP BY date, practice_code, snomed_code, bs_name, name