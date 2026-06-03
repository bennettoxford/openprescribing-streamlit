SELECT 
    date, 
    practice_code, 
    snomed_code,
    ingredient_id,
    ing.nm AS ing_name,  
    medications.vtm_id as vtm_id,
    vtm.nm AS vtm_name,
    name, 
    SUM(items) AS items, 
    SUM(quantity) AS quantity, 
    SUM(quantity * ome.weighting) AS total_ome
FROM prescribing AS rx
INNER JOIN medications
    ON medications.id = rx.snomed_code
INNER JOIN vpi
    ON medications.vmp_id = vpi.vpid
INNER JOIN ing
    ON COALESCE(vpi.bs_subid, vpi.isid) = ing.isid
INNER JOIN read_csv_auto('{data_dir}/ome_vmp.csv') AS ome
    ON ome.vmp_id = medications.vmp_id
    AND ome.ingredient_id = COALESCE(vpi.bs_subid, vpi.isid)
INNER JOIN vtm
    ON medications.vtm_id = vtm.vtmid
GROUP BY date, practice_code, snomed_code, ingredient_id, ing_name, name, vtm_id, vtm_name