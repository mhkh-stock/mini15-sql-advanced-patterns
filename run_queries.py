"""Build demo.db and run + verify all 10 Mini #15 queries.

Run:  python3 run_queries.py
Writes: data/demo.db, outputs/*.txt (one per query, headers on),
        outputs/SUMMARY.md (answers summary, generated from the run).
Asserts (exit 1 on failure):
  - base data: 12 customers, 9 products, 32 orders, 52 lines
  - every query returns >= 1 row
  - Q01: 8 spine months, revenue sums to 346,800, Jul/Aug are 0
  - Q02: 23 ordering streaks, longest is 2 months, 7 customers hit it;
    streak months sum to 31 distinct customer-months (Hassan Raza
    ordered twice in March 2026, so 31 not 32)
  - Q03: running totals and 3-month moving averages match hand calc
  - Q04: 32 orders, 22 gaps, min 22 / max 102 / avg 53.64 days;
    LAG month-over-month agrees with Mini #10 Q10 (Jun +29.22%)
  - Q05: quartiles sized 3/3/2/2, top quartile = Ayesha/Bilal/Fatima,
    their spend sums to 147,400; median cross-check 34,450
  - Q06: pivot row totals = monthly revenue, column totals = category
    totals, grand total 346,800; Jan Furniture 0, Feb Stationery 0
  - Q07: 15 rows (1 EXCEPT + 7 INTERSECT + 7 UNION); all-6-months
    INTERSECT is empty, Mouse/Notebook each sold in 5 months
  - Q08: 14 pairs, top pair Keyboard+Mug 4 orders / PKR 53,200,
    pair incidences sum to 22
  - Q09: 5 rows, grand total 346,800, category shares match
  - Q10: 7 customers cover 80% (80.65%), final share 100.00%
"""
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
fails = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}: {name} {detail}")
    if not cond:
        fails.append(name)


def main():
    db = BASE / "data" / "demo.db"
    if db.exists():
        db.unlink()
    (BASE / "outputs").mkdir(exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript((BASE / "data" / "schema.sql").read_text())
    con.executescript((BASE / "data" / "seed.sql").read_text())
    con.commit()

    counts = dict(zip(
        ["customers", "products", "orders", "lines"],
        [con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ["customers", "products", "orders", "order_items"]]))
    check("base data counts", counts == {"customers": 12, "products": 9,
                                         "orders": 32, "lines": 52}, str(counts))

    results = {}
    for path in sorted((BASE / "sql").glob("*.sql")):
        cur = con.execute(path.read_text())
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        results[path.stem[:2]] = (cols, rows)
        out = BASE / "outputs" / f"{path.stem[:2]}_{path.stem[3:]}.txt"
        with open(out, "w") as f:
            f.write(" | ".join(cols) + "\n")
            for r in rows:
                f.write(" | ".join(str(v) for v in r) + "\n")
        print(f"ran {path.name}: {len(rows)} rows -> {out.name}")

    check("every query returns >= 1 row",
          all(len(v[1]) >= 1 for v in results.values()),
          str({k: len(v[1]) for k, v in results.items()}))

    # Q01 — recursive month spine Jan–Aug 2026
    q01 = results["01"][1]
    check("Q01 spine months = 8", len(q01) == 8)
    check("Q01 revenue sums to 346800",
          sum(r[2] for r in q01) == 346800, f"({sum(r[2] for r in q01)})")
    check("Q01 Jul/Aug 2026 show 0 revenue (no orders)",
          q01[6] == ("2026-07", 0, 0) and q01[7] == ("2026-08", 0, 0),
          str(q01[6:]))
    check("Q01 Jan 37100, Jun 94200",
          q01[0][2] == 37100 and q01[5][2] == 94200)
    check("Q01 orders across spine = 32",
          sum(r[1] for r in q01) == 32, f"({sum(r[1] for r in q01)})")

    # Q02 — gaps and islands: consecutive months with an order
    q02 = results["02"][1]
    check("Q02 ordering streaks (islands) = 23", len(q02) == 23)
    check("Q02 streak months sum to 31 distinct customer-months",
          sum(r[3] for r in q02) == 31, f"({sum(r[3] for r in q02)})")
    check("Q02 31 not 32: Hassan Raza ordered twice in March 2026",
          con.execute(
              """SELECT COUNT(*) FROM orders
                 WHERE customer_id = 6
                 AND strftime('%Y-%m', order_date) = '2026-03'"""
          ).fetchone()[0] == 2)
    check("Q02 longest streak = 2 months (nobody hit 3)",
          max(r[3] for r in q02) == 2)
    two_month = {r[0] for r in q02 if r[3] == 2}
    check("Q02 7 customers have a 2-month streak",
          len(two_month) == 7, str(sorted(two_month)))
    ayesha = [r for r in q02 if r[0] == "Ayesha Khan" and r[3] == 2]
    check("Q02 Ayesha's 2-month streak is Jan–Feb 2026",
          len(ayesha) == 1 and ayesha[0][1] == "2026-01"
          and ayesha[0][2] == "2026-02", str(ayesha))

    # Q03 — window frames: running total + 3-month moving average
    q03 = results["03"][1]
    check("Q03 months = 6", len(q03) == 6)
    check("Q03 running totals match hand calc",
          [r[2] for r in q03] == [37100, 87100, 117600, 179700, 252600, 346800],
          str([r[2] for r in q03]))
    check("Q03 3-month moving averages match hand calc",
          [r[3] for r in q03] == [37100.0, 43550.0, 39200.0,
                                  47533.33, 55166.67, 76400.0],
          str([r[3] for r in q03]))
    check("Q03 final running total = 346800", q03[-1][2] == 346800)

    # Q04 — LAG: days between a customer's consecutive orders
    q04 = results["04"][1]
    check("Q04 one row per order = 32", len(q04) == 32)
    gaps = [r[4] for r in q04 if r[4] is not None]
    check("Q04 gaps = 22 (32 orders - 10 first orders)", len(gaps) == 22)
    check("Q04 first order per customer has NULL gap",
          sum(1 for r in q04 if r[4] is None) == 10)
    check("Q04 min gap 22 days, max gap 102 days",
          min(gaps) == 22 and max(gaps) == 102, f"({min(gaps)}, {max(gaps)})")
    check("Q04 average gap = 53.64 days",
          round(sum(gaps) / len(gaps), 2) == 53.64,
          f"({round(sum(gaps) / len(gaps), 2)})")
    zainab = [r for r in q04 if r[0] == "Zainab Ali" and r[4] == 102]
    check("Q04 longest gap is Zainab Ali, 102 days (12 Feb -> 25 May)",
          len(zainab) == 1, str(zainab))
    # Same LAG pattern on monthly revenue must agree with Mini #10 Q10
    mom = con.execute(
        """SELECT month, revenue_pkr,
                  LAG(revenue_pkr) OVER (ORDER BY month) AS prev_pkr,
                  ROUND(100.0 * (revenue_pkr - LAG(revenue_pkr)
                        OVER (ORDER BY month))
                        / LAG(revenue_pkr) OVER (ORDER BY month), 2) AS pct
           FROM (SELECT strftime('%Y-%m', o.order_date) AS month,
                        SUM(oi.quantity * oi.unit_price_at_sale) AS revenue_pkr
                 FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                 GROUP BY month)""").fetchall()
    check("Q04 LAG month-over-month agrees with Mini #10 Q10 (Jun +29.22%)",
          mom[-1] == ("2026-06", 94200, 72900, 29.22), str(mom[-1]))

    # Q05 — NTILE quartiles + PERCENT_RANK
    q05 = results["05"][1]
    check("Q05 customers = 10", len(q05) == 10)
    sizes = [sum(1 for r in q05 if r[3] == q) for q in (1, 2, 3, 4)]
    check("Q05 quartile sizes = 3/3/2/2", sizes == [3, 3, 2, 2], str(sizes))
    q1 = [r[0] for r in q05 if r[3] == 1]
    check("Q05 top quartile = Ayesha, Bilal, Fatima",
          q1 == ["Ayesha Khan", "Bilal Ahmed", "Fatima Noor"], str(q1))
    check("Q05 top-quartile spend sums to 147400",
          sum(r[1] for r in q05 if r[3] == 1) == 147400,
          f"({sum(r[1] for r in q05 if r[3] == 1)})")
    check("Q05 percent_rank: top 0.0, bottom 1.0",
          q05[0][4] == 0.0 and q05[-1][4] == 1.0,
          f"({q05[0][4]}, {q05[-1][4]})")
    totals = sorted(t for (t,) in con.execute(
        """SELECT SUM(oi.quantity * oi.unit_price_at_sale)
           FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
           GROUP BY o.customer_id""").fetchall())
    median = (totals[len(totals) // 2 - 1] + totals[len(totals) // 2]) / 2
    check("Q05 median cross-check = 34450 (agrees with Mini #10 Q09)",
          median == 34450, f"({median})")

    # Q06 — conditional-aggregation pivot, revenue by category per month
    q06 = results["06"][1]
    check("Q06 months = 6", len(q06) == 6)
    check("Q06 row totals = monthly revenue",
          [r[5] for r in q06] == [37100, 50000, 30500, 62100, 72900, 94200],
          str([r[5] for r in q06]))
    check("Q06 column totals = category totals",
          [sum(r[i] for r in q06) for i in (1, 2, 3, 4)]
          == [104000, 105600, 31200, 106000],
          str([sum(r[i] for r in q06) for i in (1, 2, 3, 4)]))
    check("Q06 grand total = 346800",
          sum(r[5] for r in q06) == 346800)
    check("Q06 Jan Furniture = 0, Feb Stationery = 0 (honest zeros)",
          q06[0][2] == 0 and q06[1][3] == 0)

    # Q07 — UNION / EXCEPT / INTERSECT across quarters
    q07 = results["07"][1]
    check("Q07 rows = 15 (1 + 7 + 7)", len(q07) == 15)
    by_op = {}
    for r in q07:
        by_op.setdefault(r[0], []).append(r[2])
    check("Q07 EXCEPT branch = 1 row: Ali Nawaz",
          by_op.get("bought_in_Q2_not_Q1") == ["Ali Nawaz"],
          str(by_op.get("bought_in_Q2_not_Q1")))
    check("Q07 INTERSECT branch = 7 products, no Office Chair",
          len(by_op.get("sold_in_both_quarters", [])) == 7
          and "Office Chair" not in by_op.get("sold_in_both_quarters", []),
          str(by_op.get("sold_in_both_quarters")))
    check("Q07 UNION branch = 7 products, has Office Chair, no Keyboard",
          len(by_op.get("sold_in_Jan_or_Jun", [])) == 7
          and "Office Chair" in by_op.get("sold_in_Jan_or_Jun", [])
          and "Mechanical Keyboard" not in by_op.get("sold_in_Jan_or_Jun", []),
          str(by_op.get("sold_in_Jan_or_Jun")))
    all_months = con.execute(
        """SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-01'
           INTERSECT SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-02'
           INTERSECT SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-03'
           INTERSECT SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-04'
           INTERSECT SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-05'
           INTERSECT SELECT product_id FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
           WHERE strftime('%Y-%m',o.order_date)='2026-06'""").fetchall()
    check("Q07 all-6-months INTERSECT is empty (no product sold every month)",
          all_months == [])
    months_sold = dict(con.execute(
        """SELECT p.name, COUNT(DISTINCT strftime('%Y-%m', o.order_date))
           FROM products p JOIN order_items oi ON oi.product_id = p.product_id
           JOIN orders o ON o.order_id = oi.order_id
           GROUP BY p.product_id""").fetchall())
    check("Q07 best products sold in 5 of 6 months (Mouse, Notebook Set)",
          max(months_sold.values()) == 5
          and {k for k, v in months_sold.items() if v == 5}
          == {"Wireless Mouse", "Notebook Set"}, str(months_sold))

    # Q08 — self-join: products bought together
    q08 = results["08"][1]
    check("Q08 product pairs = 14", len(q08) == 14)
    check("Q08 top pair = Keyboard + Mug Set, 4 orders, PKR 53200",
          q08[0] == ("Mechanical Keyboard", "Ceramic Mug Set", 4, 53200),
          str(q08[0]))
    check("Q08 pair incidences sum to 22",
          sum(r[2] for r in q08) == 22, f"({sum(r[2] for r in q08)})")
    check("Q08 every pair revenue > 0",
          all(r[3] > 0 for r in q08))

    # Q09 — rollup-style subtotals via UNION ALL
    q09 = results["09"][1]
    check("Q09 rows = 4 categories + grand total", len(q09) == 5)
    check("Q09 grand total row = 346800, share 100.0",
          q09[-1] == ("ALL CATEGORIES", 346800, 100.0, 1), str(q09[-1]))
    check("Q09 category revenues match",
          {r[0]: r[1] for r in q09[:4]}
          == {"Kitchen": 106000, "Furniture": 105600,
              "Electronics": 104000, "Stationery": 31200},
          str({r[0]: r[1] for r in q09[:4]}))
    check("Q09 category shares match",
          {r[0]: r[2] for r in q09[:4]}
          == {"Kitchen": 30.57, "Furniture": 30.45,
              "Electronics": 29.99, "Stationery": 9.0},
          str({r[0]: r[2] for r in q09[:4]}))
    check("Q09 category revenues sum to grand total",
          sum(r[1] for r in q09[:4]) == q09[-1][1])

    # Q10 — cumulative share / Pareto
    q10 = results["10"][1]
    check("Q10 customers = 10", len(q10) == 10)
    in80 = [r for r in q10 if r[4] == "yes"]
    check("Q10 top-80% group = 7 customers", len(in80) == 7)
    check("Q10 top-80% group spend = 279700",
          sum(r[1] for r in in80) == 279700,
          f"({sum(r[1] for r in in80)})")
    check("Q10 7th customer crosses 80% at 80.65%",
          q10[6][3] == 80.65 and q10[6][0] == "Hassan Raza", str(q10[6]))
    check("Q10 final cumulative share = 100.0",
          q10[-1][2] == 346800 and q10[-1][3] == 100.0, str(q10[-1]))
    check("Q10 cumulative shares strictly increase",
          all(q10[i][3] < q10[i + 1][3] for i in range(len(q10) - 1)))

    # Cross-query reconciliation
    grand = con.execute(
        "SELECT SUM(quantity * unit_price_at_sale) FROM order_items"
    ).fetchone()[0]
    check("reconciliation: Q01 total = order_items total = 346800",
          grand == 346800 == sum(r[2] for r in results["01"][1]))
    check("reconciliation: Q06 grand = Q09 grand = Q10 final cumulative",
          sum(r[5] for r in results["06"][1])
          == results["09"][1][-1][1] == results["10"][1][-1][2] == 346800)
    check("reconciliation: Q05 top-3 spend = Q10 cumulative at row 3",
          sum(r[1] for r in results["05"][1] if r[3] == 1)
          == results["10"][1][2][2] == 147400)

    write_summary(results)
    con.close()
    print(f"\n{len(fails)} failures" if fails else "\nall checks passed")
    return 1 if fails else 0


def write_summary(results):
    """Regenerate outputs/SUMMARY.md from this run's results."""
    lines = [
        "# Mini #15 — answers summary (generated by run_queries.py)",
        "",
        "SAMPLE / DEMO data only. Same shop as Mini #1 / Mini #3 / Mini #10: "
        "12 customers, 9 products, 32 orders, 52 lines, Jan–Jun 2026, "
        "PKR 346,800 total revenue. Average order value: PKR 10,837.50.",
        "",
        "| # | Question | Rows | Headline answer |",
        "|---|---|---|---|",
    ]
    headlines = {
        "01": "Month spine Jan–Aug 2026: all 6 selling months reconcile to "
              "PKR 346,800; Jul and Aug honestly show PKR 0 (no orders)",
        "02": "23 ordering streaks; longest is 2 months, shared by 7 customers; "
              "nobody ordered in 3 months running",
        "03": "Running total ends at PKR 346,800; 3-month moving average peaks "
              "in June at PKR 76,400 — growth is real, not one lucky month",
        "04": "22 gaps between consecutive orders; average 53.64 days; longest "
              "wait is Zainab Ali's 102 days (12 Feb to 25 May)",
        "05": "Top quartile: Ayesha Khan, Bilal Ahmed, Fatima Noor — "
              f"PKR {sum(r[1] for r in results['05'][1] if r[3] == 1):,} "
              "between them (42.50% of revenue)",
        "06": "Pivot reconciles: row totals are the monthly revenue, column "
              "totals are the category totals; Jan sold no Furniture, "
              "Feb sold no Stationery",
        "07": "Only Ali Nawaz first bought in Q2; 7 of 8 sold products sold in "
              "both quarters (Office Chair is Q2-only); no product sold in "
              "all 6 months",
        "08": "Top pair: Mechanical Keyboard + Ceramic Mug Set, together in "
              "4 orders (PKR 53,200); 14 pairs in total",
        "09": "Categories almost level — Kitchen PKR 106,000, Furniture "
              "PKR 105,600, Electronics PKR 104,000 — Stationery far behind "
              "at PKR 31,200",
        "10": "It takes 7 of 10 buyers to reach 80% of revenue (80.65%) — "
              "not a sharp 80-20; revenue is spread unusually evenly",
    }
    questions = {
        "01": "Monthly revenue on a complete month spine",
        "02": "Longest run of consecutive months with an order",
        "03": "Running revenue total and 3-month moving average",
        "04": "Days between a customer's consecutive orders",
        "05": "Customer spend quartiles",
        "06": "Revenue by category as columns, per month",
        "07": "Who and what crossed the quarter line",
        "08": "Products frequently bought together",
        "09": "Category subtotals plus a grand total",
        "10": "Cumulative share of revenue by customer",
    }
    for k in sorted(results):
        lines.append(f"| {k} | {questions[k]} | {len(results[k][1])} | "
                     f"{headlines[k]} |")
    lines += [
        "",
        "## Reconciliation",
        "",
        "- Monthly revenue (Q01 spine, Q03 frames, Q06 pivot rows) sums to "
        "PKR 346,800 = order_items total = Mini #1 / Mini #3 / Mini #10 "
        "verified total.",
        "- Q05's top-quartile spend (PKR 147,400) equals Q10's cumulative "
        "spend after the top 3 customers; Q06's column totals equal Q09's "
        "category subtotals.",
        "- Median spend (Q05 cross-check) is PKR 34,450, agreeing with "
        "Mini #10 Q09; LAG month-over-month (Q04 cross-check) agrees with "
        "Mini #10 Q10 (June +29.22%).",
        "- Q07's all-6-months INTERSECT is empty — no product sold in every "
        "month; the best (Wireless Mouse, Notebook Set) sold in 5 of 6.",
    ]
    (BASE / "outputs" / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("wrote outputs/SUMMARY.md")


if __name__ == "__main__":
    sys.exit(main())
