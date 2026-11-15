-- 06 — Revenue by category as columns, per month
-- (CONDITIONAL AGGREGATION PIVOT).
-- The pattern to learn: SQLite has no PIVOT keyword, so each column
-- is built by hand — SUM(CASE WHEN category = 'X' THEN revenue END).
-- The CASE filters inside the aggregation; the SUM adds only the
-- matching rows. A missing combination is NULL, so COALESCE(..., 0)
-- turns it into an honest 0 instead of a blank: January really sold
-- no Furniture, February really sold no Stationery.
-- Column totals reconcile exactly with the category totals in
-- query 09, and row totals with the monthly revenue in query 01.
WITH monthly_cat AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           p.category,
           SUM(oi.quantity * oi.unit_price_at_sale) AS revenue_pkr
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    GROUP BY month, p.category
)
SELECT month,
       COALESCE(SUM(CASE WHEN category = 'Electronics' THEN revenue_pkr END), 0) AS electronics_pkr,
       COALESCE(SUM(CASE WHEN category = 'Furniture' THEN revenue_pkr END), 0) AS furniture_pkr,
       COALESCE(SUM(CASE WHEN category = 'Stationery' THEN revenue_pkr END), 0) AS stationery_pkr,
       COALESCE(SUM(CASE WHEN category = 'Kitchen' THEN revenue_pkr END), 0) AS kitchen_pkr,
       SUM(revenue_pkr) AS total_pkr
FROM monthly_cat
GROUP BY month
ORDER BY month;
