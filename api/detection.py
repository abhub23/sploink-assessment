from collections import Counter
from typing import Dict, List, Tuple
from difflib import SequenceMatcher


LOOP_THRESHOLD = 0.7
DRIFT_THRESHOLD = 0.5
CONSECUTIVE_FAILURES_THRESHOLD = 3
FAILURE_RATE_THRESHOLD = 0.3


def get_ngrams(items: List[str], n: int) -> List[Tuple]:
    return [tuple(items[i : i + n]) for i in range(len(items) - n + 1)]


def ngram_similarity(seq1: List[str], seq2: List[str], n: int = 3) -> float:
    if not seq1 or not seq2 or len(seq1) < n or len(seq2) < n:
        return 0.0

    ngrams1 = set(get_ngrams(seq1, n))
    ngrams2 = set(get_ngrams(seq2, n))

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    return intersection / union if union > 0 else 0.0


def detect_loops(events: List[dict]) -> List[dict]:
    if len(events) < 6:
        return []

    actions = [e["action"] for e in events]
    inputs = [e["input"][:30] if e.get("input") else "" for e in events]
    combined = [f"{a}:{i}" for a, i in zip(actions, inputs)]

    issues = []
    window_size = min(5, len(combined) // 2)

    for i in range(len(combined) - window_size * 2):
        pattern1 = combined[i : i + window_size]
        pattern2 = combined[i + window_size : i + window_size * 2]

        similarity = ngram_similarity(pattern1, pattern2, n=2)
        if similarity >= LOOP_THRESHOLD:
            issues.append(
                {
                    "type": "loop",
                    "severity": "medium",
                    "description": f"Repeated behavior pattern detected (similarity: {similarity:.2f})",
                    "step_range": f"{events[i]['step']}-{events[i + window_size * 2 - 1]['step']}",
                }
            )
            break

    for i in range(len(actions) - window_size * 2):
        sim = ngram_similarity(
            actions[i : i + window_size],
            actions[i + window_size : i + window_size * 2],
            n=2,
        )
        if sim >= LOOP_THRESHOLD:
            found = False
            for issue in issues:
                if issue["type"] == "loop":
                    found = True
                    break
            if not found:
                issues.append(
                    {
                        "type": "loop",
                        "severity": "medium",
                        "description": f"Repeated action sequence detected (similarity: {sim:.2f})",
                        "step_range": f"{events[i]['step']}-{events[i + window_size * 2 - 1]['step']}",
                    }
                )
            break

    return issues


def detect_drift(events: List[dict]) -> List[dict]:
    if len(events) < 6:
        return []

    issues = []

    files = [
        e.get("metadata", {}).get("file", "")
        for e in events
        if e.get("metadata", {}).get("file")
    ]
    if len(files) >= 4:
        first_chunk = files[: len(files) // 2]
        second_chunk = files[len(files) // 2 :]
        if first_chunk and second_chunk and first_chunk[0] != second_chunk[0]:
            unique_first = len(set(first_chunk))
            unique_second = len(set(second_chunk))
            if unique_first >= 2 and unique_second >= 2:
                issues.append(
                    {
                        "type": "drift",
                        "severity": "medium",
                        "description": f"Topic shift: started on {first_chunk[0]}, switched to {second_chunk[0]}",
                        "step_range": f"{events[len(events) // 2 - 1]['step']}-{events[len(events) // 2]['step']}",
                    }
                )

    if len(events) < 10:
        return issues

    first_half = events[: len(events) // 2]
    second_half = events[len(events) // 2 :]

    first_actions = Counter([e["action"] for e in first_half])
    second_actions = Counter([e["action"] for e in second_half])

    first_total = sum(first_actions.values())
    second_total = sum(second_actions.values())

    first_dominant = (
        first_actions.most_common(1)[0][0]
        if first_actions and first_actions.most_common(1)[0][1] >= 2
        else None
    )
    second_dominant = (
        second_actions.most_common(1)[0][0]
        if second_actions and second_actions.most_common(1)[0][1] >= 2
        else None
    )

    if first_dominant and second_dominant and first_dominant != second_dominant:
        dominant_changed = True
        if first_dominant in second_actions:
            second_freq = second_actions[first_dominant] / second_total
            if second_freq >= 0.4:
                dominant_changed = False

        if dominant_changed:
            issues.append(
                {
                    "type": "drift",
                    "severity": "medium",
                    "description": f"Dominant action shifted from {first_dominant} to {second_dominant}",
                    "step_range": f"{first_half[-1]['step']}-{second_half[0]['step']}",
                }
            )

    first_inputs = [e.get("input", "")[:50] for e in first_half]
    second_inputs = [e.get("input", "")[:50] for e in second_half]

    if first_inputs and second_inputs:
        sim = SequenceMatcher(None, first_inputs[-1], second_inputs[0]).ratio()
        if sim < 0.3 and sim > 0:
            issues.append(
                {
                    "type": "drift",
                    "severity": "low",
                    "description": f"Intent shift detected (input similarity: {sim:.2f})",
                    "step_range": f"{first_half[-1]['step']}-{second_half[0]['step']}",
                }
            )

    return issues


def detect_failures(events: List[dict]) -> List[dict]:
    if not events:
        return []

    issues = []
    statuses = [e.get("metadata", {}).get("status", "unknown") for e in events]

    consecutive_failures = 0
    max_consecutive = 0
    for status in statuses:
        if status == "failure":
            consecutive_failures += 1
            max_consecutive = max(max_consecutive, consecutive_failures)
        else:
            consecutive_failures = 0

    if max_consecutive >= CONSECUTIVE_FAILURES_THRESHOLD:
        issues.append(
            {
                "type": "failure",
                "severity": "high",
                "description": f"{max_consecutive} consecutive failures detected",
                "step_range": "recent",
            }
        )

    failure_count = sum(1 for s in statuses if s == "failure")
    total_with_status = sum(1 for s in statuses if s in ("success", "failure"))

    if total_with_status > 0:
        failure_rate = failure_count / total_with_status
        if failure_rate >= FAILURE_RATE_THRESHOLD:
            issues.append(
                {
                    "type": "failure",
                    "severity": "high",
                    "description": f"High failure rate: {failure_rate:.1%}",
                    "step_range": "session-wide",
                }
            )

    return issues


def analyze_session(events: List[dict]) -> dict:
    all_issues = []

    all_issues.extend(detect_loops(events))
    all_issues.extend(detect_drift(events))
    all_issues.extend(detect_failures(events))

    statuses = [e.get("metadata", {}).get("status", "unknown") for e in events]
    success_count = sum(1 for s in statuses if s == "success")
    failure_count = sum(1 for s in statuses if s == "failure")

    action_dist = Counter([e["action"] for e in events])

    if any(i["severity"] == "high" for i in all_issues):
        status = "failing"
    elif any(i["type"] == "loop" for i in all_issues):
        status = "looping"
    elif any(i["type"] == "drift" for i in all_issues):
        status = "drifting"
    else:
        status = "healthy"

    return {
        "session_id": events[0].get("session_id", "unknown") if events else "unknown",
        "issues": all_issues,
        "status": status,
        "metrics": {
            "total_steps": len(events),
            "success_count": success_count,
            "failure_count": failure_count,
            "action_distribution": dict(action_dist),
        },
    }
