-- 08 — Products frequently bought together (SELF-JOIN).
-- The pattern to learn: join a table to itself. Here order_items is
-- joined to order_items on the same order_id, with
-- product_id > product_id so each pair appears once (never a product
-- with itself, never the same pair twice in reverse). The pair's
-- revenue is both lines added together in the orders where they
-- appear side by side.
-- Finding: Mechanical Keyboard + Ceramic Mug Set is the shop's
-- classic pair — together in 4 orders, PKR 53,200 of pair revenue.
-- Desk Lamp + Ceramic Mug Set is next (3 orders). 14 pairs exist in
-- total; the other 9 appear together only once.
SELECT a.name AS product_a, b.name AS product_b,
       COUNT(DISTINCT oi1.order_id) AS orders_together,
       SUM(oi1.quantity * oi1.unit_price_at_sale
         + oi2.quantity * oi2.unit_price_at_sale) AS pair_revenue_pkr
FROM order_items AS oi1
JOIN order_items AS oi2
  ON oi2.order_id = oi1.order_id
 AND oi2.product_id > oi1.product_id
JOIN products AS a ON a.product_id = oi1.product_id
JOIN products AS b ON b.product_id = oi2.product_id
GROUP BY oi1.product_id, oi2.product_id
ORDER BY orders_together DESC, pair_revenue_pkr DESC;
