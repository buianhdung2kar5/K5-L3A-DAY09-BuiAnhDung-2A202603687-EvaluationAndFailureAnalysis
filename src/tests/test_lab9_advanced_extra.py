"""Extra M5-M7 checks beyond the public vectors: traps a hidden grader may try."""
import copy

import pytest

pytestmark = pytest.mark.student


def _rep(items=3, seeds=(1, 2), **over):
    rows = [{"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i == 0 else []}
            for i in range(items) for s in seeds]
    rep = {"manifest": {"eval_set_sha": "x", "items": items, "seeds": list(seeds)}, "rows": rows,
           "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}
    rep.update(over)
    return rep


SPEC = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True,
                                               "threshold": {"min": 0.8, "no_significant_drop": True}}],
        "slices": [{"name": "denial", "metric": "pass_rate", "min": 0.9, "no_significant_drop": True, "blocking": True}]}


def test_clean_report_and_self_comparison_are_trusted():
    from lab9 import gate

    base = _rep()
    assert gate.integrity_check(base, base, SPEC, SPEC) == []


def test_metric_not_matching_rows_is_flagged():
    from lab9 import gate

    base, pr = _rep(), _rep()
    pr["rows"][0]["pass_rate"] = False                       # rows say 5/6 but the summary still says 1.0
    assert any("add up" in p for p in gate.integrity_check(pr, base, SPEC))


def test_duplicate_row_is_flagged_even_when_the_count_matches():
    from lab9 import gate

    base, pr = _rep(), _rep()
    pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    assert any("duplicate" in p for p in gate.integrity_check(pr, base, SPEC))


def test_evaluator_failure_on_a_green_run_is_flagged():
    from lab9 import gate

    base = _rep()
    assert gate.integrity_check(_rep(evaluator_failures=["E-001@1:Grader:boom"]), base, SPEC)


def test_relabelled_slice_is_flagged():
    from lab9 import gate

    base, pr = _rep(), _rep()
    for r in pr["rows"]:
        if r["item_id"] == "E-000":
            r["slices"] = []
    assert any("slice tags" in p for p in gate.integrity_check(pr, base, SPEC))


def test_ratchet_catches_dropped_slice_blocking_and_no_significant_drop():
    from lab9 import gate

    base = _rep()
    for edit in (lambda s: s.update(slices=[]),
                 lambda s: s["slices"][0].update(blocking=False),
                 lambda s: s["slices"][0].pop("no_significant_drop"),
                 lambda s: s["slices"][0].update(min=0.5),
                 lambda s: s["metrics"][0].update(blocking=False),
                 lambda s: s["metrics"].clear()):
        loose = copy.deepcopy(SPEC)
        edit(loose)
        assert gate.integrity_check(base, base, loose, SPEC), edit


def test_ratchet_allows_a_stricter_spec():
    from lab9 import gate

    base, strict = _rep(), copy.deepcopy(SPEC)
    strict["metrics"][0]["threshold"]["min"] = 0.9
    assert gate.integrity_check(base, base, strict, SPEC) == []


def test_slice_check_ignores_a_regression_outside_the_slice_and_blocks_an_empty_slice():
    from lab9 import gate

    base = _rep()
    pr = _rep()
    pr["rows"][-1]["pass_rate"] = False                      # E-002, not in slice
    assert gate.slice_check(pr, base, SPEC)[0] == []
    empty = copy.deepcopy(pr)
    for r in empty["rows"]:
        r["slices"] = []
    assert gate.slice_check(empty, base, SPEC)[0] == ["slice:denial/pass_rate"]


def test_pass_k_edge_values():
    import math

    from lab9 import stats

    assert math.isclose(stats.pass_hat_k(5, 5, 5), 1.0) and stats.pass_hat_k(5, 4, 5) == 0.0
    assert stats.pass_at_k(5, 0, 5) == 0.0 and stats.pass_at_k(5, 1, 5) == 1.0
    with pytest.raises(ValueError):
        stats.pass_hat_k(5, 6, 1)
