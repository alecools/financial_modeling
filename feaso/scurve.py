"""S-curve distribution logic for spreading costs over time periods.

Supported curve types:
- Evenly Split: equal amounts per period
- Manual S-curve 1: reverse-engineered development cost profile
- Manual S-curve 2/3: placeholder (falls back to Manual 1)
- 18/24/26/30/36 Month Build: beta-distribution based construction curves
"""

from __future__ import annotations

import numpy as np
from typing import Optional


# ── Manual S-curve 1 cumulative percentages ──────────────────────────
# Reverse-engineered from the Development Costs row in !!! - Cashflow.
# These represent the cumulative % of total cost at each relative month
# within a 32-month span (the typical development cost window).
# The profile ramps up, plateaus in the middle, then tails off.

_MANUAL_SCURVE_1_CUM_PCT = np.array([
    0.005, 0.015, 0.030, 0.055, 0.085,   # months 1-5:  slow ramp
    0.120, 0.160, 0.205, 0.255, 0.310,   # months 6-10: accelerating
    0.365, 0.420, 0.475, 0.530, 0.580,   # months 11-15: peak rate
    0.630, 0.675, 0.720, 0.760, 0.795,   # months 16-20: plateau
    0.825, 0.855, 0.880, 0.905, 0.925,   # months 21-25: decelerating
    0.942, 0.957, 0.970, 0.980, 0.988,   # months 26-30: tail
    0.995, 1.000,                          # months 31-32: completion
])


def _manual_scurve_1_weights(span: int) -> np.ndarray:
    """Generate incremental weights for Manual S-curve 1, stretched to *span* months."""
    if span <= 0:
        return np.array([])
    if span == 1:
        return np.array([1.0])

    # Interpolate cumulative percentages to the desired span
    source_x = np.linspace(0, 1, len(_MANUAL_SCURVE_1_CUM_PCT))
    target_x = np.linspace(0, 1, span)
    cum_interp = np.interp(target_x, source_x, _MANUAL_SCURVE_1_CUM_PCT)

    # Convert cumulative to incremental
    incremental = np.diff(cum_interp, prepend=0.0)
    # Normalise to sum to 1
    total = incremental.sum()
    if total > 0:
        incremental /= total
    return incremental


def _beta_scurve_weights(span: int, alpha: float = 2.0, beta: float = 5.0) -> np.ndarray:
    """Generate weights from a beta distribution PDF (construction S-curve).

    The beta distribution with α < β is right-skewed (front-loaded),
    which matches typical construction cost profiles: ramp up fast, then tail off.
    """
    if span <= 0:
        return np.array([])
    if span == 1:
        return np.array([1.0])

    from scipy.stats import beta as beta_dist

    # Evaluate PDF at midpoints of each period
    x = np.linspace(0, 1, span + 1)
    midpoints = (x[:-1] + x[1:]) / 2
    weights = beta_dist.pdf(midpoints, alpha, beta)
    total = weights.sum()
    if total > 0:
        weights /= total
    return weights


def _evenly_split_weights(span: int) -> np.ndarray:
    """Equal weight per period."""
    if span <= 0:
        return np.array([])
    return np.ones(span) / span


# ── Curve type registry ──────────────────────────────────────────────

def _get_weights(scurve_type: str, span: int) -> np.ndarray:
    """Return normalised weights for a given curve type and span."""
    stype = scurve_type.strip().lower()

    if stype == "evenly split":
        return _evenly_split_weights(span)

    elif stype in ("manual s-curve 1", "manual s-curve 2", "manual s-curve 3"):
        return _manual_scurve_1_weights(span)

    elif "month build" in stype:
        # Extract the nominal build months (e.g., "36 month build" → 36)
        # But the actual span may differ; beta curve stretches to fit
        return _beta_scurve_weights(span, alpha=2.0, beta=5.0)

    else:
        # Default: evenly split
        return _evenly_split_weights(span)


# ── Public API ───────────────────────────────────────────────────────

def distribute(
    total: float,
    scurve_type: str,
    start: int,
    span: int,
    num_periods: int,
    *,
    weights_override: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Distribute *total* across *num_periods* using the specified S-curve.

    Parameters
    ----------
    total : float
        Total amount to distribute.
    scurve_type : str
        One of "Evenly Split", "Manual S-curve 1", "36 Month Build", etc.
    start : int
        1-based period index where distribution begins.
    span : int
        Number of periods over which to distribute.
    num_periods : int
        Total number of periods in the output array.
    weights_override : np.ndarray, optional
        If provided, use these weights instead of computing from scurve_type.

    Returns
    -------
    np.ndarray
        Array of length *num_periods* with distributed amounts.
        Uses 0-based indexing (period 1 → index 0, etc.).
    """
    result = np.zeros(num_periods)
    if total == 0 or span <= 0:
        return result

    if weights_override is not None:
        weights = weights_override
    else:
        weights = _get_weights(scurve_type, span)

    amounts = total * weights

    # Place into result array (start is 1-based → index = start - 1)
    idx_start = start - 1
    for i, amount in enumerate(amounts):
        idx = idx_start + i
        if 0 <= idx < num_periods:
            result[idx] += amount

    return result


def distribute_lump_sum(
    amount: float,
    period: int,
    num_periods: int,
) -> np.ndarray:
    """Place a lump-sum amount at a single period.

    Parameters
    ----------
    amount : float
        The amount to place.
    period : int
        1-based period index.
    num_periods : int
        Total periods in the output array.
    """
    result = np.zeros(num_periods)
    idx = period - 1
    if 0 <= idx < num_periods:
        result[idx] = amount
    return result
