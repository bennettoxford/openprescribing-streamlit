WITH gbg AS (
    SELECT *
    FROM medications
    WHERE SUBSTR(bnf_code, 10, 2) = 'AA'
      AND id != vmp_id
)
SELECT
    date,
    practice_code,
    snomed_code,
    SUM(items) AS items
FROM prescribing
INNER JOIN gbg
    ON gbg.id = prescribing.snomed_code
GROUP BY date, practice_code, snomed_code