SELECT 
    date, 
    practice_code, 
    snomed_code,
    name, 
    SUM(items) AS items, 
    SUM(quantity) AS quantity, 
    SUM(actual_cost) AS actual_cost
FROM prescribing AS rx
INNER JOIN medications
    ON medications.id = rx.snomed_code
WHERE medications.vmp_id = 17313111000001106
GROUP BY date, practice_code, snomed_code, name