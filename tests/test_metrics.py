"""Metric-math tests for AgentEval on hand-computed inputs."""

import pytest

from metrics import (
    action_match,
    cost_usd,
    estimate_tokens,
    percentile,
    summarize,
    token_f1,
    tokenize,
)


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Hello, World! 123") == ["hello", "world", "123"]


def test_estimate_tokens_counts_words():
    assert estimate_tokens("one two three") == 3
    assert estimate_tokens("") == 0


def test_token_f1_perfect_overlap():
    # expected {refund, invoice} both found: P=2/4, R=1.0 -> F1=2/3
    assert token_f1(["refund", "invoice"], "refund and invoice here") == pytest.approx(2 / 3)


def test_token_f1_partial_overlap():
    # expected {a,b,c,d}, found {a,b,x,y}: P=0.5, R=0.5 -> F1=0.5
    assert token_f1(["a", "b", "c", "d"], "a b x y") == 0.5


def test_token_f1_no_overlap_is_zero():
    assert token_f1(["refund"], "hello world") == 0.0


def test_token_f1_empty_expected_is_zero():
    assert token_f1([], "anything at all") == 0.0


def test_action_match_case_insensitive():
    assert action_match("answered", "Answered") is True
    assert action_match("answered", "handoff") is False


def test_cost_usd_hand_computed():
    # 1M input tokens + 1M output tokens = 0.15 + 0.60 = 0.75
    assert cost_usd(1_000_000, 1_000_000) == 0.75
    assert cost_usd(0, 0) == 0.0


def test_percentile_nearest_rank():
    vals = [1.0, 2.0, 3.0, 4.0]
    assert percentile(vals, 50) == 2.0
    assert percentile(vals, 99) == 4.0
    assert percentile([], 50) == 0.0


def test_summarize_aggregates():
    items = [
        {"ticket_id": "A", "action": "answered", "action_correct": True,
         "answer_f1": 1.0, "latency_s": 0.1, "input_tokens": 10,
         "output_tokens": 20, "cost_usd": 0.00000165},
        {"ticket_id": "B", "action": "handoff", "action_correct": False,
         "answer_f1": 0.0, "latency_s": 0.3, "input_tokens": 10,
         "output_tokens": 0, "cost_usd": 0.0000015},
    ]
    s = summarize(items)
    assert s["n"] == 2
    assert s["action_accuracy"] == 0.5
    assert s["mean_answer_f1"] == 0.5
    assert s["latency_p50_s"] == 0.1
    assert s["latency_p99_s"] == 0.3
    assert s["total_input_tokens"] == 20
    assert s["total_output_tokens"] == 20
    assert s["cost_per_ticket_usd"] == round((0.00000165 + 0.0000015) / 2, 6)
