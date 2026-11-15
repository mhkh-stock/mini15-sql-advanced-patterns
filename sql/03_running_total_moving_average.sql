-- 03 — Running revenue total and 3-month moving average (WINDOW FRAMES).
-- The pattern to learn: a window function looks at a "frame" — a slice
-- of rows around the current one — and the frame is yours to choose.
-- ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW makes the running
-- total grow month by month; ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
-- makes a 3-month moving average that smooths out the March dip.
-- The default frame (RANGE UNBOUNDED PRECEDING ...) would give the
-- same running total here because months are unique, but ROWS is
-- explicit and behaves the same even with tied values — say so in
-- code, not in hope.
-- June is the peak month (PKR 94,200) and also the peak 3-month
-- average (PKR 76,400): growth is real, not one lucky month.
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price_at_sale) AS revenue_pkr
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    GROUP BY month
)
SELECT month, revenue_pkr,
       SUM(revenue_pkr) OVER (
           ORDER BY month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS running_total_pkr,
       ROUND(AVG(revenue_pkr) OVER (
           ORDER BY month
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 2) AS moving_avg_3m_pkr
FROM monthly
ORDER BY month;
