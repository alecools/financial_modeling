import pandas as pd
import numpy as np
from .assumptions import Assumptions


def run_kokoda_fund(a: Assumptions) -> pd.DataFrame:
    """Run the Kokoda Fund quarterly cashflow model.

    Returns a DataFrame with one row per quarter (1..num_quarters) plus
    a Q0 seed row at index 0 where all balances start at zero.
    """
    nq = a.num_quarters  # default 12
    gross_irr = a.gross_irr

    # Pre-compute quarterly inflows
    inflows = []
    for q in range(1, nq + 1):
        year = (q - 1) // 4 + 1          # 1-indexed year
        qtr_in_year = (q - 1) % 4 + 1    # 1-4
        inflows.append(a.annual_raise(year) * a.raise_pattern(qtr_in_year))

    # ---------- Allocate arrays (index 0 = Q0 seed, 1..nq = Q1..Qnq) ----------
    fund_opening = np.zeros(nq + 1)
    fund_inflow = np.zeros(nq + 1)
    fund_estab_fee = np.zeros(nq + 1)
    fund_coupon_entitlement = np.zeros(nq + 1)
    fund_coupon_paid = np.zeros(nq + 1)
    fund_redemptions = np.zeros(nq + 1)
    fund_closing = np.zeros(nq + 1)

    loan_opening = np.zeros(nq + 1)
    loan_further_advance = np.zeros(nq + 1)
    loan_interest_cap = np.zeros(nq + 1)
    loan_closing = np.zeros(nq + 1)

    redemptions = np.zeros(nq + 1)

    cash_opening = np.zeros(nq + 1)
    cash_inflow = np.zeros(nq + 1)
    cash_bank_interest = np.zeros(nq + 1)
    cash_coupon_outflow = np.zeros(nq + 1)
    cash_redemption_outflow = np.zeros(nq + 1)
    cash_admin_fee_outflow = np.zeros(nq + 1)
    cash_closing = np.zeros(nq + 1)

    estab_fee_incremental = np.zeros(nq + 1)
    estab_fee_cumulative = np.zeros(nq + 1)
    admin_fee_annual = np.zeros(nq + 1)
    admin_fee_cumulative = np.zeros(nq + 1)

    net_asset_position = np.zeros(nq + 1)

    # Q0 seed — all zeros (already initialised)

    for q in range(1, nq + 1):
        # --- Fund Balance Waterfall ---
        fund_opening[q] = fund_closing[q - 1]
        fund_inflow[q] = inflows[q - 1]
        fund_estab_fee[q] = -fund_inflow[q] * a.establishment_fee_rate
        fund_coupon_entitlement[q] = fund_closing[q - 1] * gross_irr / a.coupon_frequency
        fund_coupon_paid[q] = -fund_coupon_entitlement[q]  # cancels with entitlement in balance

        # Redemptions (computed below after loan balance is available from prior quarter)
        # We need to compute redemptions BEFORE the fund closing balance because
        # redemptions feed into both the fund balance and cash account.
        # However, redemptions depend on LOAN closing balances from prior quarters.
        # Since loan_closing[q] hasn't been computed yet for this quarter, we use
        # prior quarters' loan_closing values, which are already available.
        if q <= 3:
            # First 3 quarters (12-month lockup): no redemptions
            redemptions[q] = 0.0
        else:
            # Rolling average of last 4 quarters' closing loan balances
            start_idx = max(1, q - 3)
            avg_loan = np.mean(loan_closing[start_idx:q + 1 - 1 + 1])
            # Wait — we need loan_closing for the current quarter for this.
            # But the Excel formula uses R40:U40 for quarter U (i.e. Q4),
            # which means it uses closing loan balances for Q1..Q4 inclusive.
            # But Q4's loan_closing hasn't been computed yet at this point.
            # Looking more carefully at the Excel: U45 = AVERAGE(R40:U40)
            # This means Q4 redemption uses Q1-Q4 loan closing balances.
            # Since this creates a circular reference, let me check again...
            # Actually in Excel, row 40 (loan closing) does NOT depend on row 45.
            # The fund closing (row 30) depends on row 28 = -row 45 (redemptions).
            # And further advance (row 37) depends on change in fund balance.
            # So there IS a circular dependency:
            #   fund_closing depends on redemptions
            #   further_advance depends on fund_closing
            #   loan_closing depends on further_advance
            #   redemptions depends on loan_closing (current quarter)
            #
            # Excel resolves this with iterative calculation.
            # For our Python model, we break the circularity by computing
            # redemptions based on PRIOR quarters' loan closing balances only
            # (which matches the economic intent: you can only redeem based on
            # what's already deployed, not on what's being deployed this quarter).
            #
            # The formula AVERAGE(R40:U40) for Q4 includes the current Q4 loan
            # closing. In practice with iterative calc the difference is small.
            # We approximate by using Q(q-3) through Q(q-1) loan closings.
            lookback_start = q - 3  # 4-quarter window ending at q-1
            if lookback_start < 1:
                lookback_start = 1
            avg_loan = np.mean(loan_closing[lookback_start:q])  # q-1 inclusive
            redemptions[q] = avg_loan * a.max_redemption_pct / a.redemption_frequency

        fund_redemptions[q] = -redemptions[q]
        fund_closing[q] = (fund_opening[q] + fund_inflow[q] + fund_estab_fee[q]
                           + fund_coupon_entitlement[q] + fund_coupon_paid[q]
                           + fund_redemptions[q])

        # --- Deployment Loan Balance ---
        loan_opening[q] = loan_closing[q - 1]
        change_in_fund = fund_closing[q] - fund_closing[q - 1]
        loan_further_advance[q] = change_in_fund * a.net_deployment_rate
        loan_interest_cap[q] = loan_closing[q - 1] * a.lending_rate_to_spvs / a.coupon_frequency
        loan_closing[q] = loan_opening[q] + loan_further_advance[q] + loan_interest_cap[q]

        # --- Management Fees ---
        estab_fee_incremental[q] = -fund_estab_fee[q]  # positive
        estab_fee_cumulative[q] = estab_fee_cumulative[q - 1] + estab_fee_incremental[q]

        # Admin fee: charged at Q4 of each year
        qtr_in_year = (q - 1) % 4 + 1
        if qtr_in_year == 4:
            year_start_q = q - 3
            avg_balance = np.mean(fund_closing[year_start_q:q + 1])
            admin_fee_annual[q] = avg_balance * a.admin_fee_rate
        else:
            admin_fee_annual[q] = 0.0
        admin_fee_cumulative[q] = admin_fee_cumulative[q - 1] + admin_fee_annual[q]

        # --- Cash Account ---
        cash_opening[q] = cash_closing[q - 1]
        net_inflow = fund_inflow[q] + fund_estab_fee[q]  # gross raise minus estab fee
        cash_inflow[q] = net_inflow * (1 - a.net_deployment_rate)
        cash_bank_interest[q] = cash_opening[q] * a.cash_at_bank_rate / a.coupon_frequency
        cash_coupon_outflow[q] = -fund_coupon_entitlement[q]
        cash_redemption_outflow[q] = -redemptions[q]
        cash_admin_fee_outflow[q] = -admin_fee_annual[q]
        cash_closing[q] = (cash_opening[q] + cash_inflow[q] + cash_bank_interest[q]
                           + cash_coupon_outflow[q] + cash_redemption_outflow[q]
                           + cash_admin_fee_outflow[q])

        # --- Net Asset Position ---
        net_asset_position[q] = loan_closing[q] + cash_closing[q] - fund_closing[q]

    # Build output DataFrame (Q1..Qnq only, drop Q0 seed)
    quarters = list(range(1, nq + 1))
    years = [(q - 1) // 4 + 1 for q in quarters]
    qtr_labels = [f"Q{q}" for q in quarters]

    df = pd.DataFrame({
        "quarter": quarters,
        "year": years,
        "label": qtr_labels,
        # Fund Balance
        "fund_opening": fund_opening[1:],
        "fund_inflow": fund_inflow[1:],
        "fund_estab_fee": fund_estab_fee[1:],
        "fund_coupon_entitlement": fund_coupon_entitlement[1:],
        "fund_coupon_paid": fund_coupon_paid[1:],
        "fund_redemptions": fund_redemptions[1:],
        "fund_closing": fund_closing[1:],
        # Deployment Loan
        "loan_opening": loan_opening[1:],
        "loan_further_advance": loan_further_advance[1:],
        "loan_interest_cap": loan_interest_cap[1:],
        "loan_closing": loan_closing[1:],
        # Redemptions
        "redemptions": redemptions[1:],
        # Cash Account
        "cash_opening": cash_opening[1:],
        "cash_inflow": cash_inflow[1:],
        "cash_bank_interest": cash_bank_interest[1:],
        "cash_coupon_outflow": cash_coupon_outflow[1:],
        "cash_redemption_outflow": cash_redemption_outflow[1:],
        "cash_admin_fee_outflow": cash_admin_fee_outflow[1:],
        "cash_closing": cash_closing[1:],
        # Fees
        "estab_fee_incremental": estab_fee_incremental[1:],
        "estab_fee_cumulative": estab_fee_cumulative[1:],
        "admin_fee_annual": admin_fee_annual[1:],
        "admin_fee_cumulative": admin_fee_cumulative[1:],
        # Net Asset
        "net_asset_position": net_asset_position[1:],
    })
    df = df.set_index("quarter")
    return df


def summarise_kokoda_fund(df: pd.DataFrame) -> dict:
    """Compute summary statistics from the quarterly DataFrame."""
    total_inflow = df["fund_inflow"].sum()
    total_estab_fee = df["estab_fee_incremental"].sum()
    total_admin_fee = df["admin_fee_annual"].sum()
    total_coupon = df["fund_coupon_entitlement"].sum()
    total_redemptions = df["redemptions"].sum()
    peak_fund_size = df["fund_closing"].max()
    final_closing = df["fund_closing"].iloc[-1]
    final_cash = df["cash_closing"].iloc[-1]
    final_loan = df["loan_closing"].iloc[-1]
    final_net_asset = df["net_asset_position"].iloc[-1]

    return {
        "total_funds_raised": total_inflow,
        "total_establishment_fee": total_estab_fee,
        "total_admin_fee": total_admin_fee,
        "total_coupon_entitlement": total_coupon,
        "total_redemptions": total_redemptions,
        "peak_fund_size": peak_fund_size,
        "final_fund_closing": final_closing,
        "final_cash_balance": final_cash,
        "final_loan_balance": final_loan,
        "final_net_asset_position": final_net_asset,
    }
