-- 02 — Longest run of consecutive months with an order, per customer
-- (GAPS AND ISLANDS).
-- The pattern to learn: turn dates into plain integers, then subtract
-- a row number. Months are numbered (year * 12 + month); ROW_NUMBER()
-- counts 1, 2, 3 ... inside each customer. For a run of consecutive
-- months both counters rise by 1 together, so (month_no - rn) stays
-- constant across the whole run — that constant IS the island. A gap
-- breaks the run and the constant changes. Grouping by the constant
-- gives one row per ordering streak ("island").
-- Finding: nobody ordered in 3 months running. The longest streak is
-- 2 months, shared by 7 of the 10 buyers; the other 3 never managed
-- two months in a row.
WITH customer_months AS (
    SELECT DISTINCT o.customer_id,
           strftime('%Y-%m', o.order_date) AS month,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 12
             + CAST(strftime('%m', o.order_date) AS INTEGER) AS month_no
    FROM orders AS o
),
numbered AS (
    SELECT customer_id, month, month_no,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY month_no) AS rn
    FROM customer_months
),
islands AS (
    SELECT customer_id, month, month_no - rn AS island_key
    FROM numbered
)
SELECT c.name AS customer,
       MIN(i.month) AS island_start,
       MAX(i.month) AS island_end,
       COUNT(*) AS streak_months
FROM islands AS i
JOIN customers AS c ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.name, i.island_key
ORDER BY streak_months DESC, c.name, island_start;
