SELECT
    bnf_name,
    hospital_trust AS hospital,
    cd_category,
    bnf_chapter,
    SUM(actual_cost) AS actual_cost,
    SUM(items) AS items
FROM hospital_prescribing as rx
CROSS JOIN bounds

WHERE date(rx.date) BETWEEN bounds.start_date AND bounds.end_date
GROUP BY
    bnf_name,
    hospital,
    cd_category,
    bnf_chapter