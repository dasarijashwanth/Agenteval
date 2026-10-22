# Cost-aware routing (Day 4)

Outcome prices: spot audit of an accepted answer $0.30, reviewer decision $1.20, handoff $4.80, escalation $8.00, wrong auto-accept penalty $6.00, plus the measured per-ticket inference cost. Full assumptions in evals/cost_routing.py.

| Gate | Coverage | Mean accepted F1 | Expected $/ticket | Total $ |
| --- | --- | --- | --- | --- |
| 0.00 | 0.5400 | 0.4408 | $2.6260 | $262.60 |
| 0.20 | 0.5400 | 0.4408 | $2.6260 | $262.60 |
| 0.25 | 0.5400 | 0.4408 | $2.6260 | $262.60 |
| 0.30 | 0.5300 | 0.4444 | $2.6350 | $263.50 |
| 0.35 | 0.4200 | 0.4747 | $2.7340 | $273.40 |
| 0.40 | 0.3300 | 0.5018 | $2.8150 | $281.50 |
| 0.45 | 0.2000 | 0.5506 | $2.9320 | $293.20 |
| 0.50 | 0.1200 | 0.6023 | $3.0040 | $300.40 |
| 0.55 | 0.0800 | 0.6534 | $3.0400 | $304.00 |
| 0.60 | 0.0500 | 0.7088 | $3.0670 | $306.70 |
| 0.70 | 0.0300 | 0.7701 | $3.0850 | $308.50 |
| 0.80 | 0.0100 | 0.8462 | $3.1030 | $310.30 |

## Chosen gate

- Gate 0.35: expected $2.7340 per ticket, coverage 0.4200, mean accepted F1 0.4747. Cheapest gate whose accepted work stays at or above the quality floor (mean F1 0.45): yes.

Regenerate with: `python evals/run_day4.py`
