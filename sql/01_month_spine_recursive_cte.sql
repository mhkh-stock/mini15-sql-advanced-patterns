-- 01 — Monthly revenue on a complete month spine (RECURSIVE CTE).
-- The pattern to learn: a RECURSIVE CTE builds rows that do not exist
-- in any table — here, one row per calendar month. The anchor row is
-- the first month in the data; each step adds one month until the
-- last month (two months past the latest order, on purpose). Joining
-- real revenue onto the spine with a LEFT JOIN keeps months with
-- zero sales visible instead of silently dropping them — a plain
-- GROUP BY month can never show a month with no orders at all.
-- Jul and Aug 2026 have no orders, so they correctly show PKR 0.
WITH RECURSIVE bounds AS (
    SELECT MIN(strftime('%Y-%m', order_date)) AS first_month,
           strftime('%Y-%m', date(MAX(order_date), '+2 months')) AS last_month
    FROM orders
),
spine(month) AS (
    SELECT first_month FROM bounds
    UNION ALL
    SELECT strftime('%Y-%m', date(month || '-01', '+1 month'))
    FROM spine, bounds
    WHERE month < bounds.last_month
),
monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(oi.quantity * oi.unit_price_at_sale) AS revenue_pkr
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    GROUP BY month
)
SELECT s.month,
       COALESCE(m.orders, 0) AS orders,
       COALESCE(m.revenue_pkr, 0) AS revenue_pkr
FROM spine AS s
LEFT JOIN monthly AS m ON m.month = s.month
ORDER BY s.month;
