"""Day 4: quality-vs-coverage curve for an acceptance gate.

The harness scores every golden ticket with an answer-quality score
(token F1 against the expected keywords). This module asks: if a team
auto-accepts an agent's "answered" results only when the quality
score clears a gate, how much work ships without review (coverage),
and how good is the work that ships (mean quality of accepted items,
and the share of accepted items whose routing action was correct)?

Honest framing: offline, the F1 score is computed exactly. A live
agent would expose a runtime proxy for it (its own confidence or a
verifier score). The curve is therefore an analysis of the gate
policy, using the harness's measured quality as the gate signal; it
shows the tradeoff shape a team accepts when it sets the gate.

Runs against the deterministic FakeAgent by default, so every number
reproduces with no services up.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval import FakeAgent, run_eval  # noqa: E402

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "golden_sets" / "helpdesk_v1.json"

GATE_THRESHOLDS = [0.0, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8]


def load_items(agent=None) -> list[dict]:
    """Run the harness once and return the per-ticket scored items."""
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["items"]
    report = run_eval(agent or FakeAgent(), golden)
    return report["items"]


def accepted(item: dict, gate: float) -> bool:
    """An item ships without review iff it was answered and clears the gate."""
    return item["action"] == "answered" and item["answer_f1"] >= gate


def curve_point(items: list[dict], gate: float) -> dict:
    """Coverage and accepted-quality numbers at one gate value."""
    shipped = [i for i in items if accepted(i, gate)]
    review = [i for i in items if i["action"] == "answered" and not accepted(i, gate)]
    n = len(items)
    return {
        "gate": gate,
        "auto_accepted": len(shipped),
        "coverage": round(len(shipped) / n, 4) if n else 0.0,
        "sent_to_reviewer": len(review),
        "mean_accepted_f1": (
            round(statistics.fmean(i["answer_f1"] for i in shipped), 4) if shipped else None
        ),
        "accepted_action_accuracy": (
            round(sum(1 for i in shipped if i["action_correct"]) / len(shipped), 4)
            if shipped
            else None
        ),
    }


def build_curve(items: list[dict], gates: list[float] = GATE_THRESHOLDS) -> list[dict]:
    return [curve_point(items, gate) for gate in gates]
