-- 04 — Days between a customer's consecutive orders (LEAD / LAG).
-- The pattern to learn: LAG() reaches back one row inside the same
-- partition — here, the customer's previous order — so each order can
-- be compared with the one before it without a self-join. The first
-- order of every customer has no previous order, so its gap columns
-- are NULL, not zero: "no previous order" is a fact, not a 0-day gap.
-- The same LAG() pattern gives month-over-month revenue change in one
-- line — LAG(revenue) OVER (ORDER BY month) — which is the cleaner
-- version of the self-join Mini #10 query 10 used; both agree
-- (June +PKR 21,300, +29.22% on May, verified in run_queries.py).
-- Finding: the average gap between a buyer's orders is 53.64 days;
-- the longest wait is Zainab Ali's 102 days (12 Feb to 25 May).
WITH order_totals AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(oi.quantity * oi.unit_price_at_sale) AS order_total_pkr
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    GROUP BY o.order_id
)
SELECT c.name AS customer,
       ot.order_date,
       ot.order_total_pkr,
       LAG(ot.order_date) OVER (
           PARTITION BY ot.customer_id ORDER BY ot.order_date
       ) AS prev_order_date,
       CAST(julianday(ot.order_date) - julianday(
           LAG(ot.order_date) OVER (
               PARTITION BY ot.customer_id ORDER BY ot.order_date
           )) AS INTEGER) AS days_since_prev_order,
       LAG(ot.order_total_pkr) OVER (
           PARTITION BY ot.customer_id ORDER BY ot.order_date
       ) AS prev_order_total_pkr,
       ot.order_total_pkr - LAG(ot.order_total_pkr) OVER (
           PARTITION BY ot.customer_id ORDER BY ot.order_date
       ) AS change_vs_prev_pkr
FROM order_totals AS ot
JOIN customers AS c ON c.customer_id = ot.customer_id
ORDER BY c.name, ot.order_date;
