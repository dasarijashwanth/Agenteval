# Reviewer-effort measurement (Day 4)

Assumptions (evals/reviewer_effort.py): spot audit of an accepted
answer 0.5 min, reviewer decision on a below-gate draft 2 min,
handoff from scratch 8 min, escalation 10 min, fully manual
baseline 8 min for every ticket. An estimate, not a time study.

## At the chosen gate (0.35)

- Auto-accepted (audit only): 42
- Sent to reviewer: 12
- Handoffs: 38; escalations: 8
- Audit minutes: 21; reviewer minutes: 24; handling minutes: 384; total human minutes: 429 per 100 tickets
- Fully manual baseline: 800 minutes. Saved: 371 minutes (46.4 percent)

Regenerate with: `python evals/run_day4.py`
