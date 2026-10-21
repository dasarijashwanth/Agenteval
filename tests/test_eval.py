"""Eval-harness tests: recall@5 wiring and the FakeAgent golden baseline."""

import json
from pathlib import Path

from eval import FakeAgent, retrieved_ids, run_eval

GOLDEN_PATH = Path(__file__).parent.parent / "golden_sets" / "helpdesk_v1.json"


class StubAgent:
    """Returns canned retrieval so recall wiring can be checked exactly."""

    def answer(self, ticket_id, subject, body):
        return {
            "answer": "refund",
            "action": "answered",
            "retrieved": [{"article_id": "b4"}, {"article_id": "b1"}],
        }


def test_retrieved_ids_normalizes_dicts_and_strings():
    assert retrieved_ids({"retrieved": [{"article_id": "b4"}, "b1"]}) == ["b4", "b1"]
    assert retrieved_ids({"answer": "x"}) is None
    assert retrieved_ids({"retrieved": []}) is None


def test_run_eval_scores_recall_at_5():
    golden = [{
        "ticket_id": "X-1",
        "ticket_subject": "Refund policy",
        "body": "How do refunds work?",
        "expected_action": "answered",
        "expected_answer_keywords": ["refund"],
        "expected_evidence": ["b4", "b6"],
    }]
    report = run_eval(StubAgent(), golden)
    item = report["items"][0]
    # Stub retrieved b4 and b1; expected b4 and b6: recall@5 = 1/2.
    assert item["recall_at_5"] == 0.5
    assert item["retrieved_top5"] == ["b4", "b1"]
    assert report["summary"]["mean_recall_at_5"] == 0.5
    assert report["summary"]["recall_at_5_n"] == 1


def test_run_eval_without_retrieval_has_no_recall():
    golden = [{
        "ticket_id": "X-2",
        "ticket_subject": "Anything",
        "body": "Body text",
        "expected_action": "handoff",
        "expected_answer_keywords": [],
        "expected_evidence": ["b4"],
    }]
    report = run_eval(FakeAgent(), golden)
    assert "recall_at_5" not in report["items"][0]
    assert "mean_recall_at_5" not in report["summary"]


def test_fake_agent_matches_golden_actions():
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["items"]
    report = run_eval(FakeAgent(), golden)
    assert report["summary"]["n"] == 100
    assert report["summary"]["action_accuracy"] == 1.0
