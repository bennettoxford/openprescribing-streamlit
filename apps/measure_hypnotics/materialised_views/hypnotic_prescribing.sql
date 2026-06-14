SELECT 
    date, 
    practice_code, 
    snomed_code,
    medications.vtm_id as vtm_id,
    vtm.nm AS vtm_name,
    name, 
    SUM(items) AS items, 
    SUM(quantity) AS quantity, 
    SUM(quantity * mg_adq_pu) AS total_adq
FROM prescribing AS rx
INNER JOIN medications
    ON medications.id = rx.snomed_code
INNER JOIN vpi
    ON medications.vmp_id = vpi.vpid
INNER JOIN ing
    ON COALESCE(vpi.bs_subid, vpi.isid) = ing.isid
INNER JOIN read_csv_auto('{data_dir}/adq_vmp.csv') AS adq
    ON adq.vmp_id = medications.vmp_id
INNER JOIN vtm
    ON medications.vtm_id = vtm.vtmid
GROUP BY date, practice_code, snomed_code, name, vtm_id, vtm_name