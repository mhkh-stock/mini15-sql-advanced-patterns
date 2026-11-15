# Mini #15 — SQL Advanced Patterns Pack

**Status:** built and verified locally. Not yet published on GitHub.

**SAMPLE / DEMO data only.** Fictional shop, fictional people, fictional orders.
Never claimed as real client or real business data.

The fourth pack in the SQL series, after Mini #1's window functions,
Mini #3's CTEs & joins, and Mini #10's subqueries & EXISTS: the
advanced patterns working analysts reach for every week — recursive
CTEs, gaps and islands, window frames, `LAG`, `NTILE`, pivots, set
operators, self-joins, hand-built rollups, and Pareto analysis.
One business question per file, one named pattern per file.

## Demo dataset

The exact same shop as Mini #1, Mini #3, and Mini #10 — no new rows
invented: 12 customers (2 never ordered) · 9 products (1 never sold) ·
32 orders · 52 order lines · Jan–Jun 2026 · PKR 346,800 total revenue,
identical to all three earlier packs, so all four reconcile with each
other. Schema: `data/schema.sql` · Seed: `data/seed.sql` · Dictionary:
`data/README.md` · Built database: `data/demo.db` (rebuild any time
with `python3 run_queries.py`, which also verifies every query).

## What the pack teaches

| Pattern | What it does | Queries |
|---|---|---|
| Recursive CTE | Builds rows that do not exist in any table (a date spine) | 01 |
| Gaps and islands | Finds runs of consecutive values with `month_no − ROW_NUMBER()` | 02 |
| Window frames | `ROWS BETWEEN` chooses the exact slice a window function sees | 03 |
| `LAG` / `LEAD` | Reaches one row back (or forward) inside a partition | 04 |
| `NTILE` / `PERCENT_RANK` | Splits ranked rows into buckets / positions on a 0–1 scale | 05 |
| Conditional aggregation | `SUM(CASE WHEN ...)` pivots rows into columns | 06 |
| `UNION` / `EXCEPT` / `INTERSECT` | Compares whole result sets | 07 |
| Self-join | Joins a table to itself to find pairs | 08 |
| `UNION ALL` subtotals | Hand-built rollup (SQLite has no `ROLLUP`) | 09 |
| Cumulative share (Pareto) | Running total over a ranking, divided by the grand total | 10 |

## How to run (3 steps)

1. `cd mini15-sql-advanced-patterns`
2. `python3 run_queries.py` — builds `data/demo.db`, runs all 10
   queries, writes `outputs/*.txt` and `outputs/SUMMARY.md`, and
   asserts the checks below
3. Run any query by hand, e.g.
   `sqlite3 -header -column data/demo.db < sql/08_products_bought_together_self_join.sql`

Requires Python 3 + SQLite (standard library only). Verified on
SQLite 3.45.1.

## Queries

| File | Business question | Teaches | Verified output |
|---|---|---|---|
| `sql/01_month_spine_recursive_cte.sql` | What is monthly revenue on a complete calendar spine, including months with no sales? | Recursive CTE | 8 rows (Jan–Aug 2026); Jul and Aug honestly show PKR 0; six selling months sum to PKR 346,800 |
| `sql/02_ordering_streaks_gaps_and_islands.sql` | What is each customer's longest run of consecutive months with an order? | Gaps and islands | 23 streaks; longest is 2 months, shared by 7 customers; nobody ordered 3 months running |
| `sql/03_running_total_moving_average.sql` | How does revenue build up, and what is the 3-month moving average? | Window frames (`ROWS BETWEEN`) | 6 rows; running total ends at PKR 346,800; 3-month average peaks in June at PKR 76,400 |
| `sql/04_days_between_orders_lag.sql` | How long does each customer wait between orders? | `LAG` | 32 rows; 22 gaps, average 53.64 days; longest wait is Zainab Ali's 102 days (12 Feb to 25 May) |
| `sql/05_spend_quartiles_ntile.sql` | Which spend quartile is each customer in? | `NTILE` / `PERCENT_RANK` | 10 rows, quartiles sized 3/3/2/2; top quartile (Ayesha, Bilal, Fatima) spent PKR 147,400 |
| `sql/06_category_pivot_by_month.sql` | What is revenue by category, as columns, per month? | Conditional aggregation pivot | 6 rows; row totals are the monthly revenue, column totals are the category totals; Jan sold no Furniture, Feb sold no Stationery |
| `sql/07_quarter_sets_union_except_intersect.sql` | Who and what crossed the quarter line? | `UNION` / `EXCEPT` / `INTERSECT` | 15 rows; only Ali Nawaz first bought in Q2; 7 of 8 sold products sold in both quarters (Office Chair is Q2-only) |
| `sql/08_products_bought_together_self_join.sql` | Which products are bought together? | Self-join | 14 pairs; top pair Mechanical Keyboard + Ceramic Mug Set, together in 4 orders (PKR 53,200) |
| `sql/09_category_subtotals_union_all.sql` | What are the category subtotals and the grand total? | `UNION ALL` rollup workaround | 5 rows; Kitchen PKR 106,000 (30.57%), Furniture PKR 105,600 (30.45%), Electronics PKR 104,000 (29.99%), Stationery PKR 31,200 (9.00%) |
| `sql/10_cumulative_share_pareto.sql` | How many customers does it take to reach 80% of revenue? | Cumulative share / Pareto | 10 rows; 7 of 10 buyers to reach 80% (80.65%) — not a sharp 80-20 |

## Verification (done before delivery)

- All 10 files execute against `data/demo.db` with no errors;
  `run_queries.py` re-asserts 59 checks on every run, all passing.
- Reconciliation: monthly revenue (queries 01, 03, 06) sums to 346,800 =
  order_items total = Mini #1 / Mini #3 / Mini #10 verified total.
- Cross-pack agreement: query 05's median cross-check (PKR 34,450)
  agrees with Mini #10 query 09; query 04's `LAG` month-over-month
  (June +29.22%) agrees with Mini #10 query 10; query 05's top-3 spend
  (PKR 147,400) equals query 10's cumulative spend after the top 3.
- Query 06's pivot column totals equal query 09's category subtotals;
  query 02's streak months sum to 31 distinct customer-months, not 32,
  because Hassan Raza ordered twice in March 2026 (verified in code).
- Query 07's all-6-months `INTERSECT` is honestly empty — no product
  sold in every month; the best (Wireless Mouse, Notebook Set) sold in
  5 of 6. The empty result is asserted, not hidden.
- Verified outputs are saved in `outputs/` (one `.txt` per query
  plus `SUMMARY.md`); `run_queries.py` regenerates them on every run.

## Limits

- SAMPLE / DEMO data only — fictional shop, Jan–Jun 2026, SQLite only.
- SQLite has NO `ROLLUP` and NO `GROUPING SETS` — query 09 builds the
  grand total with `UNION ALL` instead, and says so in the file.
  SQLite also has NO `PIVOT` — query 06 builds columns with
  `SUM(CASE WHEN ...)` instead.
- Query 01's spine runs two months past the latest order (Jul–Aug
  2026) on purpose, so the zero-sales rows are visible; on a longer
  dataset the spine follows the data (it is anchored on `MIN` /
  `MAX(order_date)`).
- Query 07 compares Q1 (Jan–Mar) against Q2 (Apr–Jun) because the
  data covers Jan–Jun 2026 only — there is no second half to compare
  against, and the query says so instead of pretending otherwise.
- Query 02 counts distinct customer-months: a customer ordering twice
  in one month (Hassan Raza, March 2026) still counts as one month in
  a streak.
- Query 04's first order per customer has NULL gap columns (no
  previous order), not zero.
- Query 10's "top 80%" group is the smallest set whose cumulative
  share reaches 80% — 7 customers at 80.65%.

## Published

Not yet published — local build only, ready for the publisher.
The built `data/demo.db` is intentionally not uploaded — rebuild it
any time with `python3 run_queries.py`.
