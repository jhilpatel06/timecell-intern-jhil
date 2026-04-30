import copy


def compute_risk_metrics(portfolio):
    total_value = portfolio["total_value_inr"]
    monthly_expenses = portfolio["monthly_expenses_inr"]
    assets = portfolio["assets"]

    post_crash_value = 0
    max_risk = -1
    largest_risk_asset = None
    concentration_warning = False

    for asset in assets:
        allocation = asset["allocation_pct"]
        crash = asset["expected_crash_pct"]

        # Validate allocation
        if allocation < 0 or allocation > 100:
            raise ValueError(f"Invalid allocation for {asset['name']}")

        # Check concentration
        if allocation > 40:
            concentration_warning = True

        # Compute asset value
        asset_value = total_value * allocation / 100

        # Apply crash
        post_crash_asset_value = asset_value * (1 + crash / 100)
        post_crash_value += post_crash_asset_value

        # Risk score
        risk_score = abs(allocation * crash)
        if risk_score > max_risk:
            max_risk = risk_score
            largest_risk_asset = asset["name"]

    # Runway calculation
    if monthly_expenses <= 0:
        runway_months = float("inf")
    else:
        runway_months = post_crash_value / monthly_expenses

    ruin_test = "PASS" if runway_months > 12 else "FAIL"

    return {
        "post_crash_value": round(post_crash_value, 2),
        "runway_months": round(runway_months, 2),
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning
    }


def apply_moderate_crash(portfolio):
    new_portfolio = copy.deepcopy(portfolio)

    for asset in new_portfolio["assets"]:
        asset["expected_crash_pct"] *= 0.5

    return new_portfolio


def print_results(title, results):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

    for key, value in results.items():
        print(f"{key:25}: {value}")


def print_allocation_bar_chart(portfolio):
    print("\nPortfolio Allocation:\n")

    for asset in portfolio["assets"]:
        name = asset["name"]
        pct = asset["allocation_pct"]

        bar = "█" * int(pct // 2)  # scale down for display
        print(f"{name:10} | {bar} ({pct}%)")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
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

    # Base scenario
    base_results = compute_risk_metrics(portfolio)

    # Moderate crash scenario
    moderate_portfolio = apply_moderate_crash(portfolio)
    moderate_results = compute_risk_metrics(moderate_portfolio)

    # Print results
    print_results("Severe Crash Scenario", base_results)
    print_results("Moderate Crash Scenario", moderate_results)

    # Show allocation
    print_allocation_bar_chart(portfolio)