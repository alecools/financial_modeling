"""Stamp duty and land tax rate tables for VIC and QLD."""

from __future__ import annotations

from typing import List, Tuple


# ── Rate table type: list of (threshold, base_tax, marginal_rate) ────
# Each bracket: if value > threshold, tax = base_tax + (value - threshold) * marginal_rate
# Brackets are ordered ascending; use the highest applicable bracket.

# ── QLD Stamp Duty (Transfer Duty) ───────────────────────────────────
# Brackets sourced from QLD OSR schedule (general rates, not concession)
_QLD_STAMP_DUTY_BRACKETS: List[Tuple[float, float, float]] = [
    (0,           0.0,         0.0150),   # $0 – $5,000
    (5_000,       75.0,        0.0250),   # $5,001 – $75,000
    (75_000,      1_825.0,     0.0300),   # $75,001 – $540,000
    (540_000,     15_775.0,    0.0450),   # $540,001 – $1,000,000
    (1_000_000,   36_475.0,    0.0575),   # $1,000,001+
]

# ── VIC Stamp Duty (Land Transfer Duty) ──────────────────────────────
_VIC_STAMP_DUTY_BRACKETS: List[Tuple[float, float, float]] = [
    (0,           0.0,         0.014),    # $0 – $25,000
    (25_000,      350.0,       0.024),    # $25,001 – $130,000
    (130_000,     2_870.0,     0.050),    # $130,001 – $960,000
    (960_000,     44_370.0,    0.055),    # $960,001 – $2,000,000
    (2_000_000,   101_570.0,   0.065),    # $2,000,001+
]

# ── QLD Land Tax ─────────────────────────────────────────────────────
_QLD_LAND_TAX_BRACKETS: List[Tuple[float, float, float]] = [
    (0,           0.0,         0.000),    # $0 – $600,000 (nil)
    (600_000,     0.0,         0.010),    # $600,001 – $1,000,000
    (1_000_000,   4_000.0,     0.0165),   # $1,000,001 – $3,000,000
    (3_000_000,   37_000.0,    0.0125),   # $3,000,001 – $5,000,000
    (5_000_000,   62_000.0,    0.0175),   # $5,000,001 – $10,000,000
    (10_000_000,  149_500.0,   0.0275),   # $10,000,001+
]

# ── VIC Land Tax ─────────────────────────────────────────────────────
_VIC_LAND_TAX_BRACKETS: List[Tuple[float, float, float]] = [
    (0,           0.0,         0.000),    # $0 – $300,000 (nil)
    (300_000,     0.0,         0.002),    # $300,001 – $600,000
    (600_000,     600.0,       0.005),    # $600,001 – $1,000,000
    (1_000_000,   2_600.0,     0.008),    # $1,000,001 – $1,800,000
    (1_800_000,   9_000.0,     0.013),    # $1,800,001 – $3,000,000
    (3_000_000,   24_600.0,    0.0225),   # $3,000,001+
]


def _calc_from_brackets(
    value: float,
    brackets: List[Tuple[float, float, float]],
) -> float:
    """Calculate tax/duty from a bracket table.

    Iterates from the highest bracket downward and returns as soon as the
    value exceeds a threshold.
    """
    if value <= 0:
        return 0.0
    # Walk backwards to find the applicable bracket
    for threshold, base_tax, rate in reversed(brackets):
        if value > threshold:
            return base_tax + (value - threshold) * rate
    return 0.0


# ── Public API ───────────────────────────────────────────────────────

def calc_qld_stamp_duty(dutiable_value: float) -> float:
    """Calculate QLD transfer duty on a given dutiable value."""
    return _calc_from_brackets(dutiable_value, _QLD_STAMP_DUTY_BRACKETS)


def calc_vic_stamp_duty(dutiable_value: float) -> float:
    """Calculate VIC land transfer duty on a given dutiable value."""
    return _calc_from_brackets(dutiable_value, _VIC_STAMP_DUTY_BRACKETS)


def calc_qld_land_tax(taxable_value: float) -> float:
    """Calculate QLD land tax on a given unimproved land value."""
    return _calc_from_brackets(taxable_value, _QLD_LAND_TAX_BRACKETS)


def calc_vic_land_tax(taxable_value: float) -> float:
    """Calculate VIC land tax on a given site value."""
    return _calc_from_brackets(taxable_value, _VIC_LAND_TAX_BRACKETS)


def calc_stamp_duty(state: str, dutiable_value: float) -> float:
    """Calculate stamp duty for the given state."""
    state = state.upper().strip()
    if state == "QLD":
        return calc_qld_stamp_duty(dutiable_value)
    elif state == "VIC":
        return calc_vic_stamp_duty(dutiable_value)
    else:
        raise ValueError(f"Unsupported state for stamp duty: {state}")


def calc_land_tax(state: str, taxable_value: float) -> float:
    """Calculate land tax for the given state."""
    state = state.upper().strip()
    if state == "QLD":
        return calc_qld_land_tax(taxable_value)
    elif state == "VIC":
        return calc_vic_land_tax(taxable_value)
    else:
        raise ValueError(f"Unsupported state for land tax: {state}")
