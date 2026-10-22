"""Day 4: cost-aware routing for the acceptance gate.

Prices every routing outcome in dollars and picks the acceptance gate
that minimizes expected total cost subject to a quality floor on the
auto-accepted work (mean accepted F1 at or above the floor).

Cost model (assumptions, stated so they can be argued with):

- inference: the harness's measured per-ticket token cost (mock
  provider prices in metrics.py, about $0.00001 per ticket). Real but
  negligible next to labor; it is included so the accounting is total.
- auto-accepted answer: a 0.5 minute spot audit at a $36/hour loaded
  reviewer rate: $0.30.
- answered but below the gate: a reviewer reads the ticket and the
  draft and decides: 2 minutes, $1.20.
- handoff: a human handles the ticket from scratch: 8 minutes, $4.80.
- escalate: senior handling: 10 minutes at $48/hour, $8.00.
- wrong auto-accept penalty: an accepted answer whose routing action
  was wrong ships a bad outcome: $6.00 of rework and follow-up. The
  penalty is what stops the optimizer from just opening the gate.

Dollars are planning numbers for comparing gates on the same golden
set, not accounting figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from quality_coverage import accepted, curve_point  # noqa: E402  (sibling in evals/)

AUDIT_USD = 0.30
REVIEW_USD = 1.20
HANDOFF_USD = 4.80
ESCALATE_USD = 8.00
WRONG_ACCEPT_PENALTY_USD = 6.00
QUALITY_FLOOR_MEAN_F1 = 0.45


def item_cost_usd(item: dict, gate: float) -> float:
    """Total cost of one scored item under the gate policy."""
    cost = item["cost_usd"]  # measured inference cost
    if item["action"] == "answered":
        if accepted(item, gate):
            cost += AUDIT_USD
            if not item["action_correct"]:
                cost += WRONG_ACCEPT_PENALTY_USD
        else:
            cost += REVIEW_USD
    elif item["action"] == "escalate":
        cost += ESCALATE_USD
    else:
        cost += HANDOFF_USD
    return cost


def expected_cost(items: list[dict], gate: float) -> dict:
    """Expected total and per-ticket cost at one gate value."""
    total = sum(item_cost_usd(i, gate) for i in items)
    point = curve_point(items, gate)
    return {
        "gate": gate,
        "total_cost_usd": round(total, 4),
        "expected_cost_per_ticket_usd": round(total / len(items), 4) if items else 0.0,
        "coverage": point["coverage"],
        "mean_accepted_f1": point["mean_accepted_f1"],
        "accepted_action_accuracy": point["accepted_action_accuracy"],
    }


def sweep_costs(items: list[dict], gates: list[float]) -> list[dict]:
    return [expected_cost(items, gate) for gate in gates]


def choose_gate(
    rows: list[dict], quality_floor: float = QUALITY_FLOOR_MEAN_F1
) -> dict:
    """Cheapest gate whose accepted work clears the quality floor.

    Ties break toward higher coverage. Falls back to the cheapest row
    overall (flagged) when no gate clears the floor.
    """
    qualifying = [
        r
        for r in rows
        if r["mean_accepted_f1"] is not None and r["mean_accepted_f1"] >= quality_floor
    ]
    pool = qualifying if qualifying else rows
    best = min(pool, key=lambda r: (r["expected_cost_per_ticket_usd"], -r["coverage"]))
    return {**best, "quality_floor_met": bool(qualifying)}
