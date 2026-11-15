-- 09 — Category subtotals plus a grand total
-- (ROLLUP-STYLE TOTALS VIA UNION ALL).
-- The pattern to learn: SQLite has NO ROLLUP and NO GROUPING SETS,
-- so subtotals are built by hand — one grouped query for the
-- categories, UNION ALL with one ungrouped query for the grand total.
-- The sort_key column exists only to put the grand total last; it is
-- not part of the answer. The same UNION ALL shape gives subtotals
-- at any level (month, city, customer) without any special syntax.
-- Finding: the four categories are almost level — Kitchen PKR 106,000
-- (30.57%), Furniture PKR 105,600 (30.45%), Electronics PKR 104,000
-- (29.99%) — and Stationery far behind at PKR 31,200 (9.00%).
WITH cat AS (
    SELECT p.category,
           SUM(oi.quantity * oi.unit_price_at_sale) AS revenue_pkr
    FROM products AS p
    JOIN order_items AS oi ON oi.product_id = p.product_id
    GROUP BY p.category
),
grand AS (
    SELECT SUM(quantity * unit_price_at_sale) AS revenue_pkr
    FROM order_items
)
SELECT category AS group_label, revenue_pkr,
       ROUND(100.0 * revenue_pkr / (SELECT revenue_pkr FROM grand), 2) AS share_pct,
       0 AS sort_key
FROM cat
UNION ALL
SELECT 'ALL CATEGORIES' AS group_label, revenue_pkr, 100.0 AS share_pct,
       1 AS sort_key
FROM grand
ORDER BY sort_key, revenue_pkr DESC;
