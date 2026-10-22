# Quality-vs-coverage curve (Day 4)

Golden set: 100 tickets, scored by the harness (FakeAgent baseline).
The gate auto-accepts an answered result only when its answer-quality
score (token F1 against expected keywords) clears the gate. Offline the
score is exact; a live agent would expose a runtime proxy for it.

| Gate | Auto-accepted | Coverage | Mean accepted F1 | Accepted action accuracy | Sent to reviewer |
| --- | --- | --- | --- | --- | --- |
| 0.00 | 54 | 0.5400 | 0.4408 | 1.0000 | 0 |
| 0.20 | 54 | 0.5400 | 0.4408 | 1.0000 | 0 |
| 0.25 | 54 | 0.5400 | 0.4408 | 1.0000 | 0 |
| 0.30 | 53 | 0.5300 | 0.4444 | 1.0000 | 1 |
| 0.35 | 42 | 0.4200 | 0.4747 | 1.0000 | 12 |
| 0.40 | 33 | 0.3300 | 0.5018 | 1.0000 | 21 |
| 0.45 | 20 | 0.2000 | 0.5506 | 1.0000 | 34 |
| 0.50 | 12 | 0.1200 | 0.6023 | 1.0000 | 42 |
| 0.55 | 8 | 0.0800 | 0.6534 | 1.0000 | 46 |
| 0.60 | 5 | 0.0500 | 0.7088 | 1.0000 | 49 |
| 0.70 | 3 | 0.0300 | 0.7701 | 1.0000 | 51 |
| 0.80 | 1 | 0.0100 | 0.8462 | 1.0000 | 53 |

Reading the curve: raising the gate ships less work without review,
and the work that does ship scores higher on the quality metric.
Coverage falls smoothly here because answered-ticket scores spread
across the range instead of clustering at one value.

Regenerate with: `python evals/run_day4.py`
