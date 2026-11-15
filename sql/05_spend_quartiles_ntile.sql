-- 05 — Customer spend quartiles (NTILE / PERCENT_RANK).
-- The pattern to learn: NTILE(4) splits the ranked rows into 4
-- roughly equal buckets — quartile 1 is the top spenders, quartile 4
-- the bottom. PERCENT_RANK() gives each customer's exact position on
-- a 0-to-1 scale: 0.00 is the top spender, 1.00 the bottom. Both are
-- computed over the same ORDER BY, so they always agree with each
-- other — and with Mini #10 query 09's median (PKR 34,450), which
-- falls between quartiles 2 and 3.
-- Finding: the top quartile (Ayesha, Bilal, Fatima) spent PKR 147,400
-- between them — 42.50% of all revenue from 3 of 10 buyers.
WITH spend AS (
    SELECT c.customer_id, c.name,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(oi.quantity * oi.unit_price_at_sale) AS total_spend_pkr
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
    JOIN order_items AS oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.name
)
SELECT name AS customer, total_spend_pkr, orders,
       NTILE(4) OVER (ORDER BY total_spend_pkr DESC) AS spend_quartile,
       ROUND(PERCENT_RANK() OVER (ORDER BY total_spend_pkr DESC), 2) AS percent_rank
FROM spend
ORDER BY total_spend_pkr DESC;
