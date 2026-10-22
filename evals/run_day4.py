"""Day 4 CLI: quality-vs-coverage curve, cost-aware gate, reviewer effort.

Usage:
    python evals/run_day4.py

Writes, from a real harness run over the 100-ticket golden set:
- evals/quality_coverage_results.json / .md
- evals/cost_routing_results.json / .md
- evals/reviewer_effort_results.json / .md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cost_routing import (  # noqa: E402
    AUDIT_USD,
    ESCALATE_USD,
    HANDOFF_USD,
    QUALITY_FLOOR_MEAN_F1,
    REVIEW_USD,
    WRONG_ACCEPT_PENALTY_USD,
    choose_gate,
    sweep_costs,
)
from quality_coverage import GATE_THRESHOLDS, build_curve, load_items  # noqa: E402
from reviewer_effort import effort_for_items  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent


def _f(value) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def render_curve_md(points: list[dict], n: int) -> str:
    lines = [
        "# Quality-vs-coverage curve (Day 4)",
        "",
        f"Golden set: {n} tickets, scored by the harness (FakeAgent baseline).",
        "The gate auto-accepts an answered result only when its answer-quality",
        "score (token F1 against expected keywords) clears the gate. Offline the",
        "score is exact; a live agent would expose a runtime proxy for it.",
        "",
        "| Gate | Auto-accepted | Coverage | Mean accepted F1 | Accepted action accuracy | Sent to reviewer |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for p in points:
        lines.append(
            f"| {p['gate']:.2f} | {p['auto_accepted']} | {p['coverage']:.4f} | "
            f"{_f(p['mean_accepted_f1'])} | {_f(p['accepted_action_accuracy'])} | "
            f"{p['sent_to_reviewer']} |"
        )
    lines += [
        "",
        "Reading the curve: raising the gate ships less work without review,",
        "and the work that does ship scores higher on the quality metric.",
        "Coverage falls smoothly here because answered-ticket scores spread",
        "across the range instead of clustering at one value.",
        "",
        "Regenerate with: `python evals/run_day4.py`",
        "",
    ]
    return "\n".join(lines)


def render_cost_md(rows: list[dict], chosen: dict) -> str:
    lines = [
        "# Cost-aware routing (Day 4)",
        "",
        f"Outcome prices: spot audit of an accepted answer ${AUDIT_USD:.2f}, "
        f"reviewer decision ${REVIEW_USD:.2f}, handoff ${HANDOFF_USD:.2f}, "
        f"escalation ${ESCALATE_USD:.2f}, wrong auto-accept penalty "
        f"${WRONG_ACCEPT_PENALTY_USD:.2f}, plus the measured per-ticket "
        "inference cost. Full assumptions in evals/cost_routing.py.",
        "",
        "| Gate | Coverage | Mean accepted F1 | Expected $/ticket | Total $ |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['gate']:.2f} | {r['coverage']:.4f} | {_f(r['mean_accepted_f1'])} | "
            f"${r['expected_cost_per_ticket_usd']:.4f} | ${r['total_cost_usd']:.2f} |"
        )
    lines += [
        "",
        "## Chosen gate",
        "",
        f"- Gate {chosen['gate']:.2f}: expected "
        f"${chosen['expected_cost_per_ticket_usd']:.4f} per ticket, coverage "
        f"{chosen['coverage']:.4f}, mean accepted F1 "
        f"{_f(chosen['mean_accepted_f1'])}. Cheapest gate whose accepted work "
        f"stays at or above the quality floor (mean F1 "
        f"{QUALITY_FLOOR_MEAN_F1}): "
        f"{'yes' if chosen['quality_floor_met'] else 'no gate met the floor; cheapest overall shown'}.",
        "",
        "Regenerate with: `python evals/run_day4.py`",
        "",
    ]
    return "\n".join(lines)


def render_effort_md(effort: dict) -> str:
    lines = [
        "# Reviewer-effort measurement (Day 4)",
        "",
        "Assumptions (evals/reviewer_effort.py): spot audit of an accepted",
        "answer 0.5 min, reviewer decision on a below-gate draft 2 min,",
        "handoff from scratch 8 min, escalation 10 min, fully manual",
        "baseline 8 min for every ticket. An estimate, not a time study.",
        "",
        f"## At the chosen gate ({effort['gate']:.2f})",
        "",
        f"- Auto-accepted (audit only): {effort['auto_accepted']}",
        f"- Sent to reviewer: {effort['sent_to_reviewer']}",
        f"- Handoffs: {effort['handoffs']}; escalations: {effort['escalations']}",
        f"- Audit minutes: {effort['audit_minutes']:.0f}; reviewer minutes: "
        f"{effort['reviewer_minutes']:.0f}; handling minutes: "
        f"{effort['handling_minutes']:.0f}; total human minutes: "
        f"{effort['total_human_minutes']:.0f} per {effort['total_tickets']} tickets",
        f"- Fully manual baseline: {effort['fully_manual_baseline_minutes']:.0f} "
        f"minutes. Saved: {effort['minutes_saved']:.0f} minutes "
        f"({effort['effort_saved_pct']:.1f} percent)",
        "",
        "Regenerate with: `python evals/run_day4.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    items = load_items()
    points = build_curve(items)
    cost_rows = sweep_costs(items, GATE_THRESHOLDS)
    chosen = choose_gate(cost_rows)
    effort = effort_for_items(items, chosen["gate"])

    (EVAL_DIR / "quality_coverage_results.json").write_text(
        json.dumps({"n": len(items), "points": points}, indent=2) + "\n",
        encoding="utf-8",
    )
    (EVAL_DIR / "quality_coverage_results.md").write_text(
        render_curve_md(points, len(items)), encoding="utf-8"
    )
    (EVAL_DIR / "cost_routing_results.json").write_text(
        json.dumps(
            {
                "quality_floor_mean_f1": QUALITY_FLOOR_MEAN_F1,
                "rows": cost_rows,
                "chosen_gate": chosen,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (EVAL_DIR / "cost_routing_results.md").write_text(
        render_cost_md(cost_rows, chosen), encoding="utf-8"
    )
    (EVAL_DIR / "reviewer_effort_results.json").write_text(
        json.dumps(effort, indent=2) + "\n", encoding="utf-8"
    )
    (EVAL_DIR / "reviewer_effort_results.md").write_text(
        render_effort_md(effort), encoding="utf-8"
    )

    print(f"curve points: {len(points)} over {len(items)} tickets")
    print(
        f"chosen gate: {chosen['gate']:.2f} "
        f"(${chosen['expected_cost_per_ticket_usd']:.4f}/ticket, "
        f"mean accepted F1 {_f(chosen['mean_accepted_f1'])}, "
        f"coverage {chosen['coverage']:.4f})"
    )
    print(
        f"effort at chosen gate: {effort['total_human_minutes']:.0f} min vs "
        f"{effort['fully_manual_baseline_minutes']:.0f} baseline "
        f"({effort['effort_saved_pct']:.1f}% saved)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
