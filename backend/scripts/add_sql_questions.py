"""Add 15 prioritized SQL Q&As to questions.json (idempotent by question text)."""
import json
from pathlib import Path

QA_FILE = Path(__file__).parent.parent / "data" / "seed" / "questions.json"

NEW_QUESTIONS = [
    {
        "topic_slug": "sql",
        "question": "In production, you need the top 3 users by total spend in each product category. Walk through your approach. When would you choose ROW_NUMBER vs RANK vs DENSE_RANK?",
        "answer": """The pattern: aggregate first in a CTE, then rank within each partition, then filter.

**ROW_NUMBER**: always assigns unique sequential integers — use when you need EXACTLY N rows per group regardless of ties (tie broken arbitrarily by sort).
**RANK**: tied rows get the same rank but the next rank skips (1, 1, 3) — use when ties should both qualify and gaps are acceptable.
**DENSE_RANK**: tied rows get the same rank, no gaps (1, 1, 2) — use in leaderboards/dashboards where gaps feel wrong to users.

For "top 3 spenders per category" with ties, RANK includes all tied rows at rank 3 (may return >3 rows). ROW_NUMBER gives exactly 3. Choose based on business requirement.

**Production tip**: always pre-aggregate before windowing. Never mix `GROUP BY` aggregation and window functions in the same SELECT — you'd need a subquery anyway, so make intent explicit with a CTE.""",
        "difficulty": "medium",
        "tags": ["sql", "window-functions", "ranking", "cte"],
        "code_snippet": """```sql
WITH user_spend AS (
    SELECT
        user_id,
        category,
        SUM(amount) AS total_spend
    FROM orders
    WHERE order_status = 'completed'
    GROUP BY user_id, category
),
ranked AS (
    SELECT
        user_id,
        category,
        total_spend,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_spend DESC) AS rn,
        RANK()       OVER (PARTITION BY category ORDER BY total_spend DESC) AS rnk,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY total_spend DESC) AS drnk
    FROM user_spend
)
SELECT user_id, category, total_spend
FROM ranked
WHERE rn <= 3;   -- swap rn → rnk or drnk based on tie requirement
```""",
        "comparison_table": {
            "headers": ["Function", "Tie behavior", "Row count guarantee", "Common use case"],
            "rows": [
                ["ROW_NUMBER", "Breaks ties arbitrarily", "Exactly N rows", "Deduplication, pagination"],
                ["RANK", "Ties share rank; next rank skips", "≥ N rows possible", "Sports-style leaderboard"],
                ["DENSE_RANK", "Ties share rank; no gaps", "≥ N rows possible", "Dashboard percentile bands"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "Your PM wants a 7-day rolling average of daily signups to smooth weekend/weekday variance. Write the SQL and explain the frame specification — especially the difference between ROWS and RANGE.",
        "answer": """Use `AVG() OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`.

**ROWS BETWEEN n PRECEDING AND CURRENT ROW**: counts exactly n physical rows before the current one — deterministic and correct for time-series rolling windows.

**RANGE BETWEEN n PRECEDING AND CURRENT ROW**: counts all rows whose ORDER BY value falls within n units of the current row's value. With date ordering, if two rows have the same date both are included — this can silently produce wrong results when data has multiple rows per date.

**Always use ROWS for rolling windows on pre-aggregated data.**

**Production gap problem**: if there are days with zero signups, those days won't appear in the aggregation. The 7-day window will skip them and average over fewer real days (e.g., 5 active days out of 7). Fix with a date spine (generate_series or calendar table) to fill gaps with 0 before applying the window.""",
        "difficulty": "medium",
        "tags": ["sql", "window-functions", "time-series", "rolling-average"],
        "code_snippet": """```sql
WITH daily_signups AS (
    SELECT
        DATE_TRUNC('day', created_at) AS signup_date,
        COUNT(*) AS signups
    FROM users
    GROUP BY 1
)
SELECT
    signup_date,
    signups,
    ROUND(AVG(signups) OVER (
        ORDER BY signup_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1)  AS rolling_7d_avg,
    SUM(signups) OVER (
        ORDER BY signup_date
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_signups
FROM daily_signups
ORDER BY signup_date;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "How would you identify users who logged in for 7 or more consecutive days? Walk through the gaps-and-islands SQL pattern and explain why the date subtraction trick works.",
        "answer": """The gaps-and-islands pattern exploits this invariant: **for consecutive dates, date − ROW_NUMBER = constant**. A gap in dates breaks the arithmetic, creating a new "island."

**Steps:**
1. Deduplicate to one row per (user, date) — multiple logins on the same day count as one.
2. Assign `ROW_NUMBER()` per user ordered by date.
3. Compute `login_date − ROW_NUMBER` → this is the `island_key` (constant within a consecutive streak).
4. `GROUP BY user_id, island_key` and count rows → streak length.
5. Filter `streak_days >= 7`.

**Why it works:** If a user logs in Jan 1, 2, 3 then misses Jan 4 and logs in Jan 5, 6:
- Rows 1, 2, 3 → island_key = Jan 1 − 0, Jan 2 − 1, Jan 3 − 2 = Dec 31 (constant)
- Rows 4, 5 → island_key = Jan 5 − 3, Jan 6 − 4 = Jan 2 (different constant → new island)

**Snowflake/BigQuery note:** use `DATEADD(DAY, -ROW_NUMBER(), login_date)` instead of interval arithmetic.""",
        "difficulty": "hard",
        "tags": ["sql", "window-functions", "gaps-and-islands", "event-analytics"],
        "code_snippet": """```sql
WITH daily_logins AS (
    -- deduplicate: one row per user per day
    SELECT DISTINCT
        user_id,
        DATE(event_time) AS login_date
    FROM user_events
    WHERE event_type = 'login'
),
with_island_key AS (
    SELECT
        user_id,
        login_date,
        login_date - INTERVAL (
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) - 1
        ) DAY AS island_key
    FROM daily_logins
),
streaks AS (
    SELECT
        user_id,
        island_key,
        MIN(login_date) AS streak_start,
        MAX(login_date) AS streak_end,
        COUNT(*) AS streak_days
    FROM with_island_key
    GROUP BY user_id, island_key
)
SELECT DISTINCT user_id, streak_start, streak_end, streak_days
FROM streaks
WHERE streak_days >= 7
ORDER BY streak_days DESC;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "You have a clickstream table (user_id, event_time, event_type). How do you sessionize events where a new session begins after 30 minutes of inactivity? Explain every CTE step.",
        "answer": """Sessionization requires three steps: find time gaps, flag session boundaries, assign session IDs via cumulative sum.

**Step 1 — LAG**: for each event, look back at the user's previous event time.
**Step 2 — Flag**: if prev_event_time IS NULL (first event ever) OR gap > 30 min → mark `is_new_session = 1`.
**Step 3 — Cumulative SUM**: running sum of the flag over the user's timeline gives a monotonically increasing session number. Each increment marks a new session.

**Why cumulative SUM works:** the flag is 1 only at session boundaries. Summing it cumulatively produces a counter that increments exactly once per session — a clean surrogate session ID.

**Cross-database notes:**
- `TIMESTAMPDIFF(MINUTE, ...)` → MySQL/Snowflake
- `EXTRACT(EPOCH FROM event_time - prev_event_time)/60` → Postgres
- `DATEDIFF(MINUTE, ...)` → SQL Server

**Production tip:** Use `MD5(CONCAT(user_id, '-', session_num))` or a UUID function for globally unique session IDs if sessions are written to another table.""",
        "difficulty": "hard",
        "tags": ["sql", "sessionization", "window-functions", "event-analytics", "lag"],
        "code_snippet": """```sql
WITH lag_events AS (
    SELECT
        user_id,
        event_time,
        event_type,
        LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) AS prev_event_time
    FROM clickstream
),
session_flags AS (
    SELECT
        *,
        CASE
            WHEN prev_event_time IS NULL
              OR TIMESTAMPDIFF(MINUTE, prev_event_time, event_time) > 30
            THEN 1 ELSE 0
        END AS is_new_session
    FROM lag_events
),
with_session_id AS (
    SELECT
        *,
        SUM(is_new_session) OVER (
            PARTITION BY user_id
            ORDER BY event_time
            ROWS UNBOUNDED PRECEDING
        ) AS session_num
    FROM session_flags
)
SELECT
    user_id,
    CONCAT(user_id, '-', session_num) AS session_id,
    event_time,
    event_type
FROM with_session_id
ORDER BY user_id, event_time;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "After joining a users table to an orders table, your result has 5x more rows than users. How do you diagnose this and fix it?",
        "answer": """This is a **join cardinality explosion** — a one-to-many relationship is multiplying rows.

**Diagnosis:**
1. `SELECT COUNT(*), COUNT(DISTINCT user_id) FROM result` — if they differ, you have duplication.
2. Check right-table granularity: `SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) > 1`. If this returns rows, orders has multiple rows per user.
3. Check for duplicates in BOTH tables (many-to-many joins multiply worst).

**Fix: aggregate before joining.** Never join transaction-level data directly to a user table if you want user-level output. Pre-aggregate to the correct grain in a CTE first.

**Common mistake:** joining on a non-unique key (e.g., email instead of user_id when emails are shared across accounts).

**Production rule:** before any join, always know the cardinality of both sides — check with COUNT vs COUNT(DISTINCT key).""",
        "difficulty": "medium",
        "tags": ["sql", "joins", "debugging", "cardinality"],
        "code_snippet": """```sql
-- Wrong: joins every order row to the user → N rows per user
SELECT u.user_id, u.email, o.amount
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;

-- Fixed: aggregate orders to user grain, then join 1:1
WITH order_summary AS (
    SELECT
        user_id,
        COUNT(*)       AS order_count,
        SUM(amount)    AS total_spend,
        MAX(created_at) AS last_order_at
    FROM orders
    GROUP BY user_id
)
SELECT
    u.user_id,
    u.email,
    COALESCE(s.order_count, 0) AS order_count,
    COALESCE(s.total_spend, 0) AS total_spend
FROM users u
LEFT JOIN order_summary s ON u.user_id = s.user_id;

-- Diagnose cardinality before joining
SELECT 'orders' AS tbl, COUNT(*) AS rows, COUNT(DISTINCT user_id) AS unique_keys FROM orders;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "You wrote a LEFT JOIN to include all users even those with no orders, but the result only shows users who have orders — behaving like an INNER JOIN. What went wrong and how do you fix it?",
        "answer": """Putting a filter on the **right table's column in the WHERE clause** silently converts a LEFT JOIN to an INNER JOIN. Unmatched rows from the left table get NULL for all right-table columns — and `NULL` fails any comparison (even `NULL != 'value'`), so those rows are eliminated by WHERE.

**Rule:** conditions on the right table in a LEFT JOIN belong in the **ON clause**, not WHERE. The ON clause is evaluated during the join (NULLs survive); WHERE is evaluated after (NULLs are filtered out).

**Exception — anti-join pattern:** checking `WHERE right_table.key IS NULL` is intentional and correct — it finds left-table rows with NO match (e.g., users with no orders).""",
        "difficulty": "medium",
        "tags": ["sql", "joins", "left-join", "null-handling", "debugging"],
        "code_snippet": """```sql
-- WRONG: WHERE on right table column eliminates NULLs → becomes INNER JOIN
SELECT u.user_id, o.amount
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.status = 'completed';   -- users with no orders have o.status = NULL → filtered out

-- CORRECT: move right-table filter to ON clause
SELECT u.user_id, o.amount
FROM users u
LEFT JOIN orders o
    ON u.user_id = o.user_id
    AND o.status = 'completed';   -- join only completed orders; users with none get NULLs

-- ANTI-JOIN: users with NO completed orders (intentional NULL check)
SELECT u.user_id
FROM users u
LEFT JOIN orders o
    ON u.user_id = o.user_id AND o.status = 'completed'
WHERE o.user_id IS NULL;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "The orders table has millions of rows with multiple orders per user. You need each user's most recent order only. What are the three main approaches and their performance tradeoffs?",
        "answer": """**Approach 1 — ROW_NUMBER window (recommended):**
Single table scan, parallelizable, works at any scale. Use when you need all columns from the latest row.

**Approach 2 — Correlated MAX subquery:**
Intuitive but runs the subquery once per row — O(N²) on unindexed tables. Avoid for millions of rows.

**Approach 3 — Self-join on MAX:**
Two passes but can leverage a composite index on `(user_id, created_at)`. Breaks on ties (two orders at exact same timestamp — you'd get duplicates). Safer with a unique tiebreaker.

**Postgres bonus — DISTINCT ON:**
Most concise, single pass, works with the planner efficiently: `SELECT DISTINCT ON (user_id) * FROM orders ORDER BY user_id, created_at DESC`.

**Tie handling:** ROW_NUMBER breaks ties arbitrarily. If you need deterministic tie-breaking, add `order_id DESC` as a secondary sort key. If ties should both be returned, use RANK instead.""",
        "difficulty": "medium",
        "tags": ["sql", "window-functions", "joins", "performance", "latest-record"],
        "code_snippet": """```sql
-- Approach 1: ROW_NUMBER (recommended — single scan)
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY created_at DESC, order_id DESC  -- order_id breaks ties deterministically
        ) AS rn
    FROM orders
)
SELECT * FROM ranked WHERE rn = 1;

-- Approach 2: correlated subquery (avoid on large tables)
SELECT * FROM orders o
WHERE created_at = (
    SELECT MAX(created_at) FROM orders WHERE user_id = o.user_id
);

-- Approach 3: self-join on MAX (fast with index on user_id, created_at)
SELECT o.*
FROM orders o
JOIN (
    SELECT user_id, MAX(created_at) AS latest
    FROM orders GROUP BY user_id
) m ON o.user_id = m.user_id AND o.created_at = m.latest;

-- Postgres only: DISTINCT ON
SELECT DISTINCT ON (user_id) *
FROM orders
ORDER BY user_id, created_at DESC;
```""",
        "comparison_table": {
            "headers": ["Approach", "Passes", "Handles ties", "Scale"],
            "rows": [
                ["ROW_NUMBER", "1", "Yes (add tiebreaker)", "Best"],
                ["Correlated subquery", "N+1", "Yes (all ties)", "Avoid > 1M rows"],
                ["Self-join MAX", "2", "No (duplicates on ties)", "Good with index"],
                ["DISTINCT ON (PG)", "1", "Yes (first per ORDER BY)", "Best on Postgres"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "How would you create a training dataset for a 30-day churn prediction model in SQL? Walk through feature engineering, label creation, and how you prevent data leakage.",
        "answer": """The mental model: **every training example has a snapshot date**. Features use data strictly before that date; the label uses data strictly after it. Mixing these causes leakage.

**Three-stage pipeline:**
1. **Snapshot dates** — one observation per user per month (or fixed set of dates).
2. **Features CTE** — behavioral signals in windows of 7d, 30d, 90d ending at `< snapshot_date`.
3. **Labels CTE** — did the user have any activity in `[snapshot_date, snapshot_date + 30d)`? No = churned.

**Leakage traps to avoid:**
- Using `MAX(event_time)` without a date bound — pulls in future events.
- Using `COUNT(*)` over all events instead of windowing before snapshot.
- Joining on `event_time <= snapshot_date` without strict `<` (boundary event is neither feature nor label).

**Point-in-time correctness** is the same concept as "as-of joins" in feature stores. The SQL version is filtering every feature aggregation with `WHERE event_time >= snapshot_date - INTERVAL X AND event_time < snapshot_date`.""",
        "difficulty": "hard",
        "tags": ["sql", "ml-dataset", "data-leakage", "feature-engineering", "churn"],
        "code_snippet": """```sql
WITH snapshot_dates AS (
    -- one snapshot per user per calendar month
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('month', activity_date) AS snapshot_date
    FROM (
        SELECT DISTINCT user_id, DATE(event_time) AS activity_date
        FROM user_events
    ) t
),
features AS (
    SELECT
        s.user_id,
        s.snapshot_date,
        -- 7-day window
        COUNT(CASE WHEN e.event_time >= s.snapshot_date - INTERVAL 7 DAY
                    AND e.event_time <  s.snapshot_date THEN 1 END) AS events_7d,
        -- 30-day window
        COUNT(CASE WHEN e.event_time >= s.snapshot_date - INTERVAL 30 DAY
                    AND e.event_time <  s.snapshot_date THEN 1 END) AS events_30d,
        -- days since last event (as of snapshot)
        DATEDIFF(
            s.snapshot_date,
            MAX(CASE WHEN e.event_time < s.snapshot_date THEN e.event_time END)
        ) AS days_since_last_event
    FROM snapshot_dates s
    LEFT JOIN user_events e ON s.user_id = e.user_id
    GROUP BY s.user_id, s.snapshot_date
),
labels AS (
    SELECT
        s.user_id,
        s.snapshot_date,
        CASE
            WHEN COUNT(CASE WHEN e.event_time >= s.snapshot_date
                             AND e.event_time <  s.snapshot_date + INTERVAL 30 DAY
                             THEN 1 END) = 0
            THEN 1 ELSE 0
        END AS churned
    FROM snapshot_dates s
    LEFT JOIN user_events e ON s.user_id = e.user_id
    GROUP BY s.user_id, s.snapshot_date
)
SELECT f.*, l.churned
FROM features f
JOIN labels l USING (user_id, snapshot_date);
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "Your recommendation model needs negative training examples — items the user didn't interact with. How do you generate a balanced negative sample set in SQL? What's the difference between exposure-based and random negatives?",
        "answer": """**Exposure-based negatives (recommended when impression logs exist):**
Items the user was shown (impressed) but didn't click. These are high-quality negatives because they represent real no-interest signals under the current ranking policy.

**Random negatives (fallback when impression logs don't exist):**
Generate all (user, item) pairs via CROSS JOIN, subtract known positives via anti-join, then sample.

**Hard negatives:** items from the same category or from top-popularity lists that the user didn't interact with. They're harder for the model to distinguish from positives — forcing the model to learn fine-grained signals. Use BM25 or a previous model version to generate them.

**Sampling ratio:** typically 4:1 or 10:1 negatives-to-positives. Use `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY RAND())` to sample per-user rather than globally — ensures each user's negative:positive ratio is balanced.

**Scale warning:** CROSS JOIN over 1M users × 100K items = 100B rows. Pre-filter items to popular/recent catalog (top 10K by interactions) before crossing.""",
        "difficulty": "hard",
        "tags": ["sql", "recommender-systems", "negative-sampling", "ml-dataset", "anti-join"],
        "code_snippet": """```sql
-- Exposure-based negatives (impression logs available)
WITH positives AS (
    SELECT DISTINCT user_id, item_id FROM interactions WHERE event_type = 'click'
)
SELECT i.user_id, i.item_id, 0 AS label
FROM impressions i
LEFT JOIN positives p ON i.user_id = p.user_id AND i.item_id = p.item_id
WHERE p.user_id IS NULL;    -- seen but not clicked

-- Random negatives with 4:1 sampling ratio (when no impression log)
WITH positives AS (
    SELECT DISTINCT user_id, item_id FROM interactions
),
popular_items AS (
    SELECT item_id FROM interactions
    GROUP BY item_id ORDER BY COUNT(*) DESC LIMIT 10000
),
all_pairs AS (
    SELECT DISTINCT u.user_id, i.item_id
    FROM (SELECT DISTINCT user_id FROM interactions) u
    CROSS JOIN popular_items i
),
candidate_negatives AS (
    SELECT a.user_id, a.item_id
    FROM all_pairs a
    LEFT JOIN positives p ON a.user_id = p.user_id AND a.item_id = p.item_id
    WHERE p.user_id IS NULL
),
sampled AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY RAND()) AS rn
    FROM candidate_negatives
)
SELECT user_id, item_id, 0 AS label
FROM sampled
WHERE rn <= 4 * (SELECT COUNT(*) / COUNT(DISTINCT user_id) FROM positives);
```""",
        "comparison_table": {
            "headers": ["Negative type", "Quality", "Requires", "Use case"],
            "rows": [
                ["Exposure-based", "High (real no-click)", "Impression log", "Ranking/CTR models"],
                ["Random", "Low-medium", "Nothing", "Retrieval/recall models"],
                ["Hard negatives", "Highest", "Previous model or BM25", "Fine-tuning, embedding models"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "How do you compute experiment lift and check for sample ratio mismatch (SRM) in SQL? Why does SRM invalidate an experiment even if lift looks good?",
        "answer": """**Lift** measures the treatment effect:
- Absolute lift = treatment_CVR − control_CVR
- Relative lift = (treatment_CVR − control_CVR) / control_CVR × 100

**Sample Ratio Mismatch (SRM):** if you expected a 50/50 split but get 48/52, your randomization is broken. Causes: logging bugs, bots filtered differently per arm, redirect latency dropping treatment users. SRM makes the experiment uninterpretable — selection bias contaminates lift estimates.

**Detection:** compare actual group sizes to expected split. A deviation > 1% on large experiments is a red flag. SQL gives you the ratio; chi-square test (in Python/R) gives the p-value.

**Critical rule:** always check SRM before interpreting lift. A 5% lift with SRM is meaningless; you can't trust the number.

**Other SQL checks:** post-assignment conversion only (filter `conversion_time > assignment_time`), deduplication (one row per user per experiment arm).""",
        "difficulty": "hard",
        "tags": ["sql", "ab-testing", "experimentation", "lift", "srm"],
        "code_snippet": """```sql
-- Lift calculation
WITH group_metrics AS (
    SELECT
        a.group_name,
        COUNT(DISTINCT a.user_id)       AS users,
        SUM(COALESCE(c.converted, 0))   AS conversions,
        ROUND(100.0 * SUM(COALESCE(c.converted, 0))
              / COUNT(DISTINCT a.user_id), 4) AS cvr_pct
    FROM experiment_assignments a
    LEFT JOIN (
        SELECT DISTINCT user_id, 1 AS converted, converted_at
        FROM conversion_events
    ) c ON a.user_id = c.user_id
        AND c.converted_at > a.assigned_at   -- post-assignment only
    WHERE a.experiment_id = 'exp_2024_q3_checkout'
    GROUP BY a.group_name
)
SELECT
    t.group_name,
    t.cvr_pct                                       AS treatment_cvr,
    ctrl.cvr_pct                                    AS control_cvr,
    ROUND(t.cvr_pct - ctrl.cvr_pct, 4)             AS absolute_lift_pct,
    ROUND(100.0 * (t.cvr_pct - ctrl.cvr_pct)
          / NULLIF(ctrl.cvr_pct, 0), 2)             AS relative_lift_pct
FROM group_metrics t
CROSS JOIN group_metrics ctrl
WHERE t.group_name = 'treatment'
  AND ctrl.group_name = 'control';

-- SRM check
SELECT
    group_name,
    COUNT(DISTINCT user_id)                                             AS assigned,
    ROUND(100.0 * COUNT(DISTINCT user_id)
          / SUM(COUNT(DISTINCT user_id)) OVER (), 2)                   AS actual_share_pct,
    50.0                                                               AS expected_share_pct,
    ABS(100.0 * COUNT(DISTINCT user_id)
        / SUM(COUNT(DISTINCT user_id)) OVER () - 50.0)                AS deviation_pct
FROM experiment_assignments
WHERE experiment_id = 'exp_2024_q3_checkout'
GROUP BY group_name;
-- Flag if deviation_pct > 1.0
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "From an ad impressions table (impression_id, user_id, ad_id, position, clicked), how do you compute overall CTR, CTR by position, and detect position bias in your ranking system?",
        "answer": """**CTR = clicks / impressions.** Straightforward aggregate.

**Position bias:** users click position 1 far more than position 5, regardless of ad quality. A naive CTR comparison across ads ignores this — a good ad at position 5 with 2% CTR may outperform a mediocre ad at position 1 with 5% CTR once you normalize.

**Position-adjusted lift:** for each (ad, position), compare the ad's CTR to the average CTR at that position. A positive delta means the ad outperforms its position baseline.

**Production implications:**
- Use position-normalized CTR for model training labels — otherwise the model learns position preferences, not ad quality.
- Inverse propensity scoring (IPS) is the principled fix: weight each click by 1/P(position_shown) to debias.
- Position entropy analysis: if CTR at position 1 is 10× position 5, you have strong position bias — model calibration will be off.""",
        "difficulty": "medium",
        "tags": ["sql", "ctr", "position-bias", "ranking", "ads"],
        "code_snippet": """```sql
-- Overall CTR per ad
SELECT
    ad_id,
    COUNT(*)               AS impressions,
    SUM(clicked)           AS clicks,
    ROUND(100.0 * SUM(clicked) / COUNT(*), 4) AS ctr_pct
FROM ad_impressions
GROUP BY ad_id
ORDER BY ctr_pct DESC;

-- CTR by position (reveal position bias)
SELECT
    position,
    COUNT(*)               AS impressions,
    SUM(clicked)           AS clicks,
    ROUND(100.0 * SUM(clicked) / COUNT(*), 4) AS ctr_pct
FROM ad_impressions
GROUP BY position
ORDER BY position;

-- Position-adjusted CTR: ad CTR vs position baseline
WITH position_baseline AS (
    SELECT position, AVG(clicked * 1.0) AS baseline_ctr
    FROM ad_impressions
    GROUP BY position
),
ad_by_position AS (
    SELECT ad_id, position, AVG(clicked * 1.0) AS ad_ctr, COUNT(*) AS impressions
    FROM ad_impressions
    GROUP BY ad_id, position
    HAVING COUNT(*) >= 100   -- min impressions threshold
)
SELECT
    a.ad_id,
    a.position,
    ROUND(a.ad_ctr * 100, 4)                         AS ad_ctr_pct,
    ROUND(p.baseline_ctr * 100, 4)                   AS position_baseline_pct,
    ROUND((a.ad_ctr - p.baseline_ctr) * 100, 4)      AS position_adjusted_lift
FROM ad_by_position a
JOIN position_baseline p ON a.position = p.position
ORDER BY position_adjusted_lift DESC;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "You have a model predictions table with predicted_label and actual_label. How do you compute precision, recall, and F1-score in SQL for a binary classifier? How do you compare two model versions?",
        "answer": """Use **conditional aggregation** to compute the four cells of the confusion matrix, then derive metrics.

**Key formulas:**
- TP = predicted=1 AND actual=1
- FP = predicted=1 AND actual=0
- FN = predicted=0 AND actual=1
- TN = predicted=0 AND actual=0
- Precision = TP / (TP + FP)  ← of those predicted positive, how many are actually positive?
- Recall = TP / (TP + FN)  ← of all actual positives, how many did we catch?
- F1 = 2 × Precision × Recall / (Precision + Recall)

**Always use NULLIF(denom, 0)** to guard against division by zero — if the model predicts all negatives, TP + FP = 0 and precision is undefined.

**Multi-model comparison:** add `model_version` to GROUP BY and compute all metrics per version in a single query.""",
        "difficulty": "medium",
        "tags": ["sql", "ml-metrics", "precision", "recall", "f1", "confusion-matrix"],
        "code_snippet": """```sql
-- Single-model confusion matrix + metrics
WITH confusion AS (
    SELECT
        SUM(CASE WHEN predicted_label = 1 AND actual_label = 1 THEN 1 ELSE 0 END) AS tp,
        SUM(CASE WHEN predicted_label = 1 AND actual_label = 0 THEN 1 ELSE 0 END) AS fp,
        SUM(CASE WHEN predicted_label = 0 AND actual_label = 1 THEN 1 ELSE 0 END) AS fn,
        SUM(CASE WHEN predicted_label = 0 AND actual_label = 0 THEN 1 ELSE 0 END) AS tn
    FROM model_predictions
    WHERE model_version = 'v2'
)
SELECT
    tp, fp, fn, tn,
    ROUND(tp * 1.0 / NULLIF(tp + fp, 0), 4)                AS precision,
    ROUND(tp * 1.0 / NULLIF(tp + fn, 0), 4)                AS recall,
    ROUND(2.0 * tp / NULLIF(2 * tp + fp + fn, 0), 4)       AS f1_score,
    ROUND((tp + tn) * 1.0 / NULLIF(tp + fp + fn + tn, 0), 4) AS accuracy
FROM confusion;

-- Multi-model version comparison
SELECT
    model_version,
    ROUND(SUM(CASE WHEN predicted_label = 1 AND actual_label = 1 THEN 1.0 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN predicted_label = 1 THEN 1 ELSE 0 END), 0), 4) AS precision,
    ROUND(SUM(CASE WHEN predicted_label = 1 AND actual_label = 1 THEN 1.0 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN actual_label = 1 THEN 1 ELSE 0 END), 0), 4)   AS recall,
    COUNT(*) AS total_predictions
FROM model_predictions
GROUP BY model_version
ORDER BY model_version;
```""",
        "comparison_table": {
            "headers": ["Metric", "Formula", "Interpretation"],
            "rows": [
                ["Precision", "TP / (TP+FP)", "When model fires, how often is it right?"],
                ["Recall", "TP / (TP+FN)", "Of all true positives, how many does model catch?"],
                ["F1", "2·P·R / (P+R)", "Harmonic mean — use when classes are imbalanced"],
                ["Accuracy", "(TP+TN) / total", "Misleading on imbalanced datasets — avoid as primary metric"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "How do you build a weekly cohort retention table showing what percentage of each signup cohort is still active in weeks 1, 2, 4, and 8?",
        "answer": """Cohort retention requires three building blocks:
1. **Cohort assignment** — truncate each user's signup date to the cohort week.
2. **Week offset** — for each (user, activity week), compute how many weeks after signup that activity occurred: `DATEDIFF('week', cohort_week, activity_week)`.
3. **Retention rate** — `active_users_in_week_N / cohort_size × 100`.

**Critical join direction:** join users to activity — not the other way around. Users with zero activity in a week should still appear with 0 retention, not be dropped.

**Rolling vs cohort retention:**
- **Cohort retention**: of users who joined in week W, what % returned in week W+N? → tracks long-term engagement decay for a fixed group.
- **Rolling retention**: of all users active in week W, what % were also active in week W+1? → tracks week-over-week product health.

**Pivoting:** SQL PIVOT (Snowflake/SQL Server) or `MAX(CASE WHEN week_offset = 1 THEN retention_pct END)` to go from long to wide format.""",
        "difficulty": "hard",
        "tags": ["sql", "cohort-analysis", "retention", "window-functions", "time-series"],
        "code_snippet": """```sql
WITH user_cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC('week', created_at) AS cohort_week
    FROM users
),
user_activity AS (
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('week', event_time) AS activity_week
    FROM user_events
),
cohort_sizes AS (
    SELECT cohort_week, COUNT(*) AS cohort_size
    FROM user_cohorts
    GROUP BY cohort_week
),
weekly_retention AS (
    SELECT
        c.cohort_week,
        DATEDIFF('week', c.cohort_week, a.activity_week) AS week_offset,
        COUNT(DISTINCT a.user_id)                         AS active_users
    FROM user_cohorts c
    JOIN user_activity a ON c.user_id = a.user_id
    WHERE a.activity_week >= c.cohort_week
    GROUP BY c.cohort_week, week_offset
)
SELECT
    r.cohort_week,
    s.cohort_size,
    r.week_offset,
    r.active_users,
    ROUND(100.0 * r.active_users / s.cohort_size, 1) AS retention_pct
FROM weekly_retention r
JOIN cohort_sizes s ON r.cohort_week = s.cohort_week
WHERE r.week_offset IN (0, 1, 2, 4, 8)   -- focus weeks
ORDER BY r.cohort_week, r.week_offset;
```""",
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "sql",
        "question": "How do you compute step-by-step funnel conversion rates for a 4-step checkout flow from a user events table? What's the most common mistake in funnel SQL?",
        "answer": """**Funnel pattern:** for each user, check whether they completed each step. Then aggregate across users.

**The critical rule — use MAX, not COUNT:** if a user visits the product page 10 times, they should count as 1 person reaching step 1, not 10. Use `MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END)` per user.

**Two conversion metrics:**
- **Step-to-step CVR**: what % of users reaching step N continued to step N+1?
- **Overall CVR**: what % of users who reached step 1 completed step N?

**Ordered funnel:** for the most rigorous funnel, ensure steps happen in the correct order (e.g., cart_add must occur AFTER product_view). Add MIN(event_time) per step and check ordering. Simple boolean approach ignores order but is acceptable for most analysis.

**Common mistakes:**
1. Using COUNT instead of COUNT(DISTINCT user_id) → inflated numbers.
2. No MIN sample filter → small cohorts produce misleading 100% rates.
3. Missing users who skip steps → ensure you start from the correct entry point.""",
        "difficulty": "medium",
        "tags": ["sql", "funnel-analysis", "event-analytics", "conditional-aggregation"],
        "code_snippet": """```sql
WITH user_funnel AS (
    SELECT
        user_id,
        MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS did_view,
        MAX(CASE WHEN event_type = 'cart_add'     THEN 1 ELSE 0 END) AS did_cart,
        MAX(CASE WHEN event_type = 'checkout'     THEN 1 ELSE 0 END) AS did_checkout,
        MAX(CASE WHEN event_type = 'purchase'     THEN 1 ELSE 0 END) AS did_purchase
    FROM user_events
    WHERE event_time >= CURRENT_DATE - INTERVAL 30 DAY
    GROUP BY user_id
),
funnel_counts AS (
    SELECT
        SUM(did_view)                                           AS step1,
        SUM(did_view     * did_cart)                           AS step2,
        SUM(did_view     * did_cart * did_checkout)            AS step3,
        SUM(did_view     * did_cart * did_checkout * did_purchase) AS step4
    FROM user_funnel
)
SELECT 'product_view' AS step, step1 AS users,
    100.0                                            AS step_cvr_pct,
    100.0                                            AS overall_cvr_pct
FROM funnel_counts
UNION ALL
SELECT 'cart_add',  step2,
    ROUND(100.0 * step2 / NULLIF(step1, 0), 1),
    ROUND(100.0 * step2 / NULLIF(step1, 0), 1)
FROM funnel_counts
UNION ALL
SELECT 'checkout',  step3,
    ROUND(100.0 * step3 / NULLIF(step2, 0), 1),
    ROUND(100.0 * step3 / NULLIF(step1, 0), 1)
FROM funnel_counts
UNION ALL
SELECT 'purchase',  step4,
    ROUND(100.0 * step4 / NULLIF(step3, 0), 1),
    ROUND(100.0 * step4 / NULLIF(step1, 0), 1)
FROM funnel_counts;
```""",
        "comparison_table": None,
        "reference_urls": []
    }
]


def main():
    data = json.loads(QA_FILE.read_text())
    existing_questions = {q["question"] for q in data}
    added = 0
    for q in NEW_QUESTIONS:
        if q["question"] in existing_questions:
            print(f"  SKIP (duplicate): {q['question'][:60]}")
            continue
        data.append(q)
        existing_questions.add(q["question"])
        added += 1
        print(f"  ADD: {q['question'][:60]}")
    QA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nDone: added {added} questions. Total: {len(data)}")


if __name__ == "__main__":
    main()
