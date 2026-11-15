-- 10 — Cumulative share of revenue by customer (PARETO / 80-20).
-- The pattern to learn: order customers by spend, then run a window
-- SUM over that order — the running total divided by the grand total
-- is each customer's cumulative share. The LAG of the cumulative
-- share decides who belongs in the "top 80%" group: a customer is in
-- the group while the cumulative share BEFORE them is still under
-- 80% — the first row has no "before", so it is always in.
-- Finding: it takes 7 of the 10 buyers to reach 80% of revenue
-- (80.65%), so this shop is NOT a sharp 80-20 — revenue is spread
-- unusually evenly. The top 3 cover only 42.50% (see query 05).
WITH spend AS (
    SELECT c.name AS customer,
           SUM(oi.quantity * oi.unit_price_at_sale) AS total_spend_pkr
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
    JOIN order_items AS oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.name
),
grand AS (
    SELECT SUM(total_spend_pkr) AS revenue_pkr FROM spend
),
cum AS (
    SELECT customer, total_spend_pkr,
           SUM(total_spend_pkr) OVER (ORDER BY total_spend_pkr DESC) AS cumulative_spend_pkr
    FROM spend
)
SELECT customer, total_spend_pkr, cumulative_spend_pkr,
       ROUND(100.0 * cumulative_spend_pkr / grand.revenue_pkr, 2) AS cumulative_share_pct,
       CASE WHEN LAG(cumulative_spend_pkr) OVER (ORDER BY total_spend_pkr DESC) IS NULL
                 OR LAG(cumulative_spend_pkr) OVER (ORDER BY total_spend_pkr DESC)
                    < 0.8 * grand.revenue_pkr
            THEN 'yes' ELSE 'no' END AS in_top_80_pct_group
FROM cum, grand
ORDER BY total_spend_pkr DESC;
