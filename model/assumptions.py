from dataclasses import dataclass, field
from typing import List


@dataclass
class Assumptions:
    # --- Fundraising ---
    capital_raise_y1: float = 50.0   # $m
    capital_raise_y2: float = 100.0
    capital_raise_y3: float = 150.0
    raise_pattern_q1: float = 0.25
    raise_pattern_q2: float = 0.25
    raise_pattern_q3: float = 0.25
    raise_pattern_q4: float = 0.25

    # --- Investment Parameters ---
    cash_rate: float = 0.0435
    investment_margin: float = 0.0665
    coupon_frequency: int = 4          # quarterly
    establishment_fee_rate: float = 0.01
    admin_fee_rate: float = 0.005
    fund_term_years: int = 3

    # --- Portfolio Management ---
    net_deployment_rate: float = 0.80
    cash_at_bank_rate: float = 0.045
    lending_rate_to_spvs: float = 0.15
    initial_lockup_months: int = 12
    max_redemption_pct: float = 0.025
    redemption_frequency: int = 4      # quarterly

    # --- Underwriting Fund ---
    uw_fund_term_months: int = 36
    sell_down_pct: float = 1.0
    sell_down_months: int = 3
    gross_fund_size: float = 50.0      # $m
    loc_pct_of_fund: float = 0.50
    margin_share_net_uw: float = 0.35
    margin_share_loc: float = 0.15
    uw_preferred_return: float = 0.20876
    uw_interest_undrawn: float = 0.035
    loc_preferred_return: float = 0.19804
    loc_unused_charge: float = 0.01
    uw_admin_fee: float = 0.005
    loc_admin_fee: float = 0.0
    uw_distribution_freq: int = 2      # semi-annual

    # --- Sensitivity / Property Lending ---
    gross_return_debt: float = 0.2436
    net_investor_return_debt: float = 0.19
    wingate_estab_fee: float = 0.0175
    debt_facility_term_months: int = 18

    # --- Derived properties ---
    @property
    def gross_irr(self) -> float:
        return self.cash_rate + self.investment_margin

    @property
    def cost_of_funds(self) -> float:
        if self.net_deployment_rate == 0:
            return 0.0
        return self.gross_irr / self.net_deployment_rate

    @property
    def loc_size(self) -> float:
        return self.gross_fund_size * self.loc_pct_of_fund

    @property
    def net_uw_fund_size(self) -> float:
        return self.gross_fund_size - self.loc_size

    def annual_raise(self, year: int) -> float:
        """Return the capital raise for a given year (1-indexed)."""
        mapping = {1: self.capital_raise_y1, 2: self.capital_raise_y2, 3: self.capital_raise_y3}
        return mapping.get(year, 0.0)

    def raise_pattern(self, quarter_in_year: int) -> float:
        """Return the raise pattern fraction for a quarter within a year (1-4)."""
        mapping = {1: self.raise_pattern_q1, 2: self.raise_pattern_q2,
                   3: self.raise_pattern_q3, 4: self.raise_pattern_q4}
        return mapping.get(quarter_in_year, 0.0)

    @property
    def num_quarters(self) -> int:
        return self.fund_term_years * 4
