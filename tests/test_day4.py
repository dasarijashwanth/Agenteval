"""Day 4 tests: quality-vs-coverage curve, cost model, reviewer effort."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

from cost_routing import choose_gate, expected_cost, item_cost_usd, sweep_costs
from quality_coverage import GATE_THRESHOLDS, build_curve, curve_point, load_items
from reviewer_effort import effort_for_items


def _item(action, f1, correct=True, cost=0.00001):
    return {
        "action": action,
        "answer_f1": f1,
        "action_correct": correct,
        "cost_usd": cost,
    }


def test_curve_point_math():
    items = (
        [_item("answered", 0.9)] * 4
        + [_item("answered", 0.3)] * 2
        + [_item("handoff", 0.0)] * 3
        + [_item("escalate", 0.0)] * 1
    )
    point = curve_point(items, 0.5)
    assert point["auto_accepted"] == 4
    assert point["coverage"] == 0.4
    assert point["sent_to_reviewer"] == 2
    assert point["mean_accepted_f1"] == 0.9
    assert point["accepted_action_accuracy"] == 1.0


def test_item_cost_branches():
    gate = 0.5
    # Accepted and correct: inference + audit only.
    assert abs(item_cost_usd(_item("answered", 0.9), gate) - (0.00001 + 0.30)) < 1e-9
    # Accepted but wrong action: penalty applies.
    assert abs(
        item_cost_usd(_item("answered", 0.9, correct=False), gate)
        - (0.00001 + 0.30 + 6.00)
    ) < 1e-9
    # Below gate: reviewer cost. Handoff and escalate: handling costs.
    assert abs(item_cost_usd(_item("answered", 0.3), gate) - (0.00001 + 1.20)) < 1e-9
    assert abs(item_cost_usd(_item("handoff", 0.0), gate) - (0.00001 + 4.80)) < 1e-9
    assert abs(item_cost_usd(_item("escalate", 0.0), gate) - (0.00001 + 8.00)) < 1e-9


def test_choose_gate_respects_quality_floor():
    rows = [
        {"gate": 0.0, "mean_accepted_f1": 0.40, "coverage": 0.54,
         "expected_cost_per_ticket_usd": 2.00},
        {"gate": 0.3, "mean_accepted_f1": 0.46, "coverage": 0.50,
         "expected_cost_per_ticket_usd": 2.10},
        {"gate": 0.5, "mean_accepted_f1": 0.60, "coverage": 0.30,
         "expected_cost_per_ticket_usd": 2.40},
    ]
    chosen = choose_gate(rows)
    assert chosen["gate"] == 0.3
    assert chosen["quality_floor_met"] is True


def test_effort_math():
    items = (
        [_item("answered", 0.9)] * 4
        + [_item("answered", 0.3)] * 2
        + [_item("handoff", 0.0)] * 3
        + [_item("escalate", 0.0)] * 1
    )
    effort = effort_for_items(items, 0.5)
    # Audit 4*0.5=2, review 2*2=4, handling 3*8+1*10=34, total 40, base 80.
    assert effort["total_human_minutes"] == 40.0
    assert effort["fully_manual_baseline_minutes"] == 80.0
    assert effort["effort_saved_pct"] == 50.0


def test_real_curve_shape():
    items = load_items()
    points = build_curve(items)
    by_gate = {p["gate"]: p for p in points}
    open_gate = by_gate[0.0]
    # FakeAgent answers 54 of 100 golden tickets, all action-correct.
    assert open_gate["auto_accepted"] == 54
    assert open_gate["coverage"] == 0.54
    assert open_gate["accepted_action_accuracy"] == 1.0
    # Coverage never grows as the gate rises; accepted quality never falls.
    coverages = [p["coverage"] for p in points]
    assert coverages == sorted(coverages, reverse=True)
    f1s = [p["mean_accepted_f1"] for p in points if p["mean_accepted_f1"] is not None]
    assert f1s == sorted(f1s)


def test_real_cost_choice_meets_floor():
    items = load_items()
    rows = sweep_costs(items, GATE_THRESHOLDS)
    chosen = choose_gate(rows)
    assert chosen["quality_floor_met"] is True
    assert chosen["mean_accepted_f1"] >= 0.45
    for row in rows:
        if row["mean_accepted_f1"] is not None and row["mean_accepted_f1"] >= 0.45:
            assert row["expected_cost_per_ticket_usd"] >= chosen["expected_cost_per_ticket_usd"]


def test_real_effort_at_chosen_gate_saves_vs_manual():
    items = load_items()
    chosen = choose_gate(sweep_costs(items, GATE_THRESHOLDS))
    effort = effort_for_items(items, chosen["gate"])
    expected = expected_cost(items, chosen["gate"])
    assert effort["total_tickets"] == 100
    assert effort["total_human_minutes"] < effort["fully_manual_baseline_minutes"]
    assert effort["effort_saved_pct"] > 0
    assert (
        effort["auto_accepted"] + effort["sent_to_reviewer"]
        + effort["handoffs"] + effort["escalations"]
        == 100
    )
    assert expected["gate"] == chosen["gate"]
