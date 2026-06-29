SELECT
    icb.id || '_' || t.snomed_code AS unique_id,
    t.date AS ds,
    SUM(t.quantity)::DOUBLE AS y
FROM prescribing t
JOIN org p ON p.id = t.practice_code AND p.org_type = 'pra' AND p.inactive = 0
JOIN org_relation r1 ON r1.child_id = p.id
JOIN org pcn ON pcn.id = r1.parent_id AND pcn.org_type = 'pcn'
JOIN org_relation r2 ON r2.child_id = pcn.id
JOIN org sic ON sic.id = r2.parent_id AND sic.org_type = 'sic'
JOIN org_relation r3 ON r3.child_id = sic.id
JOIN org icb ON icb.id = r3.parent_id AND icb.org_type = 'icb'
WHERE t.date >= (SELECT MAX(date) FROM prescribing) - INTERVAL 4 YEAR
GROUP BY icb.id, t.snomed_code, t.date