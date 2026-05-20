SELECT
    rx.practice_code as practice_code,
    med.vtm_id AS vtm_id,
    vtm.nm AS vtm_name,
    med.id AS snomed_code,
    med.name AS pres_name,
    SUM(rx.items) AS items,
    SUM(rx.actual_cost) AS actual_cost
FROM prescribing rx
JOIN medications med ON rx.snomed_code = med.id
JOIN vtm vtm ON med.vtm_id = vtm.vtmid
WHERE rx.date BETWEEN '2025-01-01' AND '2025-12-01'
GROUP BY rx.practice_code, med.vtm_id, vtm.nm, med.id, med.name
