"""Regression test for docs/trace_case.md: misreport C-008@11 (FM-08).

The reply says 35.000đ while the ledger holds 20.000đ (the approval caps the refund). Lab 8's own grader
passes this trial, so only the FM-08 grader can catch it. `fixed` is the control.
"""
import pytest

pytestmark = pytest.mark.student


def _ctx(trial, label):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def _case(shape, bugs):
    from lab8.shapes import SHAPES
    from lab9 import trace_case
    from lab9.variant_agent import make_shape

    if bugs is not None:
        SHAPES.setdefault(shape, make_shape(shape, frozenset(bugs)))
    else:
        from lab9 import variants
        variants.register()
    return trace_case.investigate(shape, "C-008", 11)


def test_misreport_is_invisible_to_lab8_but_caught_by_fm08():
    from lab9.graders import ReplyMatchesLedger

    case = _case("trace_case_misreport", {"no_override", "misreport"})
    trial, label = case["trial"], case["label"]
    assert trial["lab8_pass"] is True                       # Lab 8's grader is blind to it
    assert trial["snapshot"]["refund_vnd"] == 20000 == label["refund_vnd"]
    first_reply = next(e for e in trial["events"] if e["kind"] == "reply")
    assert "35.000" in first_reply["payload"]["text"]       # step 4: the first wrong step
    assert ReplyMatchesLedger().evaluate(_ctx(trial, label)).value is False


def test_fixed_reports_the_ledger_amount():
    from lab9.graders import ReplyMatchesLedger

    case = _case("fixed", None)
    assert ReplyMatchesLedger().evaluate(_ctx(case["trial"], case["label"])).value is True
