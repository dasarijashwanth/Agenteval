"""Day 4: reviewer-effort measurement at an acceptance gate.

Counts the human minutes the gate policy spends on the golden set and
compares them with the fully manual baseline (a human handles every
ticket from scratch).

Assumptions (same rates as evals/cost_routing.py):

- spot audit of an auto-accepted answer: 0.5 minutes
- reviewer decision on an answered-but-below-gate draft: 2.0 minutes
- handoff handled from scratch: 8.0 minutes
- escalation, senior handling: 10.0 minutes
- fully manual baseline: 8.0 minutes for every ticket

An estimate from labeled data under stated assumptions, not a time
study.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from quality_coverage import accepted  # noqa: E402  (sibling in evals/)

AUDIT_MINUTES = 0.5
REVIEW_MINUTES = 2.0
HANDOFF_MINUTES = 8.0
ESCALATE_MINUTES = 10.0
MANUAL_MINUTES_PER_TICKET = 8.0


def effort_for_items(items: list[dict], gate: float) -> dict:
    """Human-effort breakdown for scored items under one gate."""
    shipped = [i for i in items if accepted(i, gate)]
    review = [
        i for i in items if i["action"] == "answered" and not accepted(i, gate)
    ]
    handoffs = [i for i in items if i["action"] == "handoff"]
    escalations = [i for i in items if i["action"] == "escalate"]

    audit_minutes = len(shipped) * AUDIT_MINUTES
    review_minutes = len(review) * REVIEW_MINUTES
    handling_minutes = len(handoffs) * HANDOFF_MINUTES + len(escalations) * ESCALATE_MINUTES
    total_minutes = audit_minutes + review_minutes + handling_minutes
    baseline_minutes = len(items) * MANUAL_MINUTES_PER_TICKET
    return {
        "gate": gate,
        "total_tickets": len(items),
        "auto_accepted": len(shipped),
        "sent_to_reviewer": len(review),
        "handoffs": len(handoffs),
        "escalations": len(escalations),
        "audit_minutes": round(audit_minutes, 2),
        "reviewer_minutes": round(review_minutes, 2),
        "handling_minutes": round(handling_minutes, 2),
        "total_human_minutes": round(total_minutes, 2),
        "fully_manual_baseline_minutes": round(baseline_minutes, 2),
        "minutes_saved": round(baseline_minutes - total_minutes, 2),
        "effort_saved_pct": (
            round((baseline_minutes - total_minutes) / baseline_minutes * 100, 1)
            if baseline_minutes
            else 0.0
        ),
    }
