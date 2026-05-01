import copy
import sys

def compute_risk_metrics(portfolio):
    # Extract core inputs from portfolio
    total_value = portfolio["total_value_inr"]
    monthly_expenses = portfolio["monthly_expenses_inr"]
    assets = portfolio["assets"]

    # Initialize aggregate metrics
    post_crash_value = 0              # total portfolio value after crash
    max_risk = -1                    # track highest risk contribution
    largest_risk_asset = None        # asset contributing most to downside
    concentration_warning = False    # flag if any asset > 40%

    for asset in assets:
        allocation = asset["allocation_pct"]
        crash = asset["expected_crash_pct"]

        # Basic validation → ensures correctness (no invalid allocations)
        if allocation < 0 or allocation > 100:
            raise ValueError(f"Invalid allocation for {asset['name']}")

        # Concentration check → required metric (>40% in single asset)
        if allocation > 40:
            concentration_warning = True

        # Convert % allocation → actual INR value
        asset_value = total_value * allocation / 100

        # Apply crash scenario (e.g., -80% → retain 20% of value)
        post_crash_asset_value = asset_value * (1 + crash / 100)
        post_crash_value += post_crash_asset_value

        # Risk contribution = allocation × crash magnitude
        # Used to identify most dangerous asset in downturn
        risk_score = abs(allocation * crash)
        if risk_score > max_risk:
            max_risk = risk_score
            largest_risk_asset = asset["name"]

    # Runway = how long portfolio can sustain expenses post-crash
    if monthly_expenses <= 0:
        runway_months = float("inf")  # edge case: no expenses
    else:
        runway_months = post_crash_value / monthly_expenses

    # Ruin test → pass if portfolio survives >12 months
    ruin_test = "PASS" if runway_months > 12 else "FAIL"

    return {
        "post_crash_value": round(post_crash_value, 2),
        "runway_months": round(runway_months, 2),
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning
    }


def apply_moderate_crash(portfolio):
    # Create a copy to avoid mutating original portfolio
    new_portfolio = copy.deepcopy(portfolio)

    # Moderate scenario = 50% of severe crash impact
    for asset in new_portfolio["assets"]:
        asset["expected_crash_pct"] *= 0.5

    return new_portfolio


def print_results(title, results):
    # Simple structured output for readability
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

    for key, value in results.items():
        print(f"{key:25}: {value}")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    
def print_allocation_bar_chart(portfolio):
    # CLI visualization → helps quickly inspect allocation distribution
    print("\nPortfolio Allocation:\n")

    for asset in portfolio["assets"]:
        name = asset["name"]
        pct = asset["allocation_pct"]

        bar = "█" * int(pct // 2)  # scaled for terminal width
        print(f"{name:10} | {bar} ({pct}%)")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    currency = "INR"
    # Sample portfolio (1 Cr INR, diversified across assets)
    portfolio = {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
        ]
    }

    # Severe crash → directly uses given expected crash values
    base_results = compute_risk_metrics(portfolio)

    # Moderate crash → reduced severity for comparison
    moderate_portfolio = apply_moderate_crash(portfolio)
    moderate_results = compute_risk_metrics(moderate_portfolio)

    # Display both scenarios side-by-side (as required in bonus)
    print_results(f"Severe Crash Scenario (Currency : {currency})", base_results)
    print_results(f"Moderate Crash Scenario (Currency : {currency})", moderate_results)

    # Optional visualization → quick sanity check of allocations
    print_allocation_bar_chart(portfolio)
