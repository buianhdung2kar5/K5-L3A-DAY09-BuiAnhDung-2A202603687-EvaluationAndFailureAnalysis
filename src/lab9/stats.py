"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    h, j = list(human), list(judge)
    if len(h) != len(j):
        raise ValueError("human and judge must have the same length")
    tp = sum(a == POS and b == POS for a, b in zip(h, j))
    fp = sum(a != POS and b == POS for a, b in zip(h, j))
    fn = sum(a == POS and b != POS for a, b in zip(h, j))
    tn = sum(a != POS and b != POS for a, b in zip(h, j))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    c = confusion(human, judge)
    p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
    r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
    return p, r


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    c = confusion(human, judge)
    n = sum(c.values())
    if n == 0:
        raise ValueError("kappa undefined: no data")
    p_o = (c["tp"] + c["tn"]) / n
    h_pos, j_pos = (c["tp"] + c["fn"]) / n, (c["tp"] + c["fp"]) / n
    p_e = h_pos * j_pos + (1 - h_pos) * (1 - j_pos)
    if p_e >= 1:
        raise ValueError("kappa undefined: p_e == 1 (constant raters)")
    return (p_o - p_e) / (1 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1
    if denom <= 0:
        raise ValueError("judge no better than chance: Rogan-Gladen undefined")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / denom))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy import stats as sps

    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.shape != y.shape:
        raise ValueError("a and b must have the same length")
    if np.array_equal(x, y):
        return (0.0, 0.0, 0.0)
    res = sps.bootstrap((x, y), lambda u, v, axis: np.mean(u, axis=axis) - np.mean(v, axis=axis),
                        paired=True, vectorized=True, n_resamples=n_resamples,
                        confidence_level=confidence, method="percentile",
                        rng=np.random.default_rng(rng))
    ci = res.confidence_interval
    return (float(x.mean() - y.mean()), float(ci.low), float(ci.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    from math import comb
    if not (0 <= c <= n) or k < 1 or k > n:
        raise ValueError("need 0 <= c <= n and 1 <= k <= n")
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    from math import comb
    if not (0 <= c <= n) or k < 1 or k > n:
        raise ValueError("need 0 <= c <= n and 1 <= k <= n")
    return comb(c, k) / comb(n, k)
