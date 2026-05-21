SELECT
    practice_code,
    snomed_code,
    SUM(quantity) as quantity
FROM prescribing
WHERE date = (SELECT MAX(date) FROM date)
    AND snomed_code IN (SELECT DISTINCT vpid FROM tariff_price_changes_price_changes)
GROUP BY practice_code, snomed_code