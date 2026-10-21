"""Metric math for AgentEval: answer quality, cost, latency, tokens."""

from __future__ import annotations

import re
import statistics

INPUT_PRICE_PER_1M = 0.15   # mock provider pricing, USD
OUTPUT_PRICE_PER_1M = 0.60  # mock provider pricing, USD

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def estimate_tokens(text: str) -> int:
    """Whitespace-ish token estimate; deterministic and dependency free."""
    return len(tokenize(text))


def token_f1(expected_keywords: list[str], answer: str) -> float:
    """F1 of expected keywords against answer tokens.

    Keywords may be multi-word phrases; each is flattened into tokens
    before the set comparison.
    """
    expected: set[str] = set()
    for keyword in expected_keywords:
        expected.update(tokenize(keyword))
    if not expected:
        return 0.0
    found = {w.lower() for w in tokenize(answer)}
    hits = expected & found
    if not hits:
        return 0.0
    precision = len(hits) / len(found)
    recall = len(hits) / len(expected)
    return 2 * precision * recall / (precision + recall)


def action_match(expected_action: str, actual_action: str) -> bool:
    return expected_action.strip().lower() == actual_action.strip().lower()


def recall_at_k(expected_ids: list[str], retrieved_ids: list[str], k: int = 5) -> float | None:
    """Fraction of expected evidence ids found in the top-k retrieved ids.

    Returns None when the ticket carries no expected evidence (nothing to
    recall), so averages can run over evidence-bearing tickets only. When
    the agent returns fewer than k results, the metric degrades to recall
    at the returned depth; the value is still reported as recall@k.
    """
    expected = set(expected_ids)
    if not expected:
        return None
    top = set(retrieved_ids[:k])
    return len(expected & top) / len(expected)


def cost_usd(input_tokens: int, output_tokens: int) -> float:
    return input_tokens / 1_000_000 * INPUT_PRICE_PER_1M + output_tokens / 1_000_000 * OUTPUT_PRICE_PER_1M


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile; pct in [0, 100]."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, int((pct / 100) * len(ordered) + 0.5))
    return ordered[min(rank, len(ordered)) - 1]


def summarize(items: list[dict]) -> dict:
    """Aggregate per-ticket item dicts into a cost-aware summary."""
    n = len(items)
    if n == 0:
        return {"n": 0}
    latencies = [i["latency_s"] for i in items]
    costs = [i["cost_usd"] for i in items]
    total_cost = sum(costs)
    summary = {
        "n": n,
        "action_accuracy": round(sum(1 for i in items if i["action_correct"]) / n, 4),
        "mean_answer_f1": round(sum(i["answer_f1"] for i in items) / n, 4),
        "latency_p50_s": round(percentile(latencies, 50), 4),
        "latency_p99_s": round(percentile(latencies, 99), 4),
        "mean_latency_s": round(statistics.fmean(latencies), 4),
        "total_input_tokens": sum(i["input_tokens"] for i in items),
        "total_output_tokens": sum(i["output_tokens"] for i in items),
        "total_cost_usd": round(total_cost, 6),
        "cost_per_ticket_usd": round(total_cost / n, 6),
    }
    recalls = [i["recall_at_5"] for i in items if i.get("recall_at_5") is not None]
    if recalls:
        summary["mean_recall_at_5"] = round(statistics.fmean(recalls), 4)
        summary["recall_at_5_n"] = len(recalls)
    return summary
