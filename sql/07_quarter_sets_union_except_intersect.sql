-- 07 — Who and what crossed the quarter line
-- (UNION / EXCEPT / INTERSECT).
-- The pattern to learn: set operators compare whole result sets.
-- EXCEPT returns rows in the first set but not the second; INTERSECT
-- returns rows in both; UNION returns rows in either (deduped).
-- The data covers Jan–Jun 2026 only, so the quarters are Q1
-- (Jan–Mar) and Q2 (Apr–Jun) — there is no second half to compare
-- against, and the query says so instead of pretending otherwise.
-- Finding: only Ali Nawaz first bought in Q2 (everyone else bought
-- in Q1 too); 7 of the 8 sold products sold in both quarters — the
-- exception is the Office Chair, a Q2-only product. A full
-- all-6-months INTERSECT is empty: no product sold in every single
-- month (Wireless Mouse and Notebook Set each sold in 5 of 6).
-- That empty result is verified in run_queries.py, not hidden.
SELECT 'bought_in_Q2_not_Q1' AS set_operation,
       'customer' AS entity_type, name AS entity
FROM (
    SELECT c.name
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
    WHERE o.order_date >= '2026-04-01'
    EXCEPT
    SELECT c.name
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
    WHERE o.order_date < '2026-04-01'
)
UNION ALL
SELECT 'sold_in_both_quarters' AS set_operation,
       'product' AS entity_type, name AS entity
FROM (
    SELECT p.name
    FROM products AS p
    JOIN order_items AS oi ON oi.product_id = p.product_id
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_date < '2026-04-01'
    INTERSECT
    SELECT p.name
    FROM products AS p
    JOIN order_items AS oi ON oi.product_id = p.product_id
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_date >= '2026-04-01'
)
UNION ALL
SELECT 'sold_in_Jan_or_Jun' AS set_operation,
       'product' AS entity_type, name AS entity
FROM (
    SELECT p.name
    FROM products AS p
    JOIN order_items AS oi ON oi.product_id = p.product_id
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE strftime('%Y-%m', o.order_date) = '2026-01'
    UNION
    SELECT p.name
    FROM products AS p
    JOIN order_items AS oi ON oi.product_id = p.product_id
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE strftime('%Y-%m', o.order_date) = '2026-06'
)
ORDER BY set_operation, entity;
