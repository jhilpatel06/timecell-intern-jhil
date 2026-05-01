# This script simulates portfolio crashes, rebalances allocations to improve survival (runway),
# and explains both the decisions and impact in simple financial terms.

import copy
import json
import os
import sys
from dotenv import load_dotenv
from groq import Groq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")


# Computes portfolio value after crash and how many months expenses can be sustained
def compute_risk_metrics(portfolio):
    total = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]

    post_crash = 0

    for a in portfolio["assets"]:
        val = total * a["allocation_pct"] / 100  # convert allocation % to actual value
        post_crash += val * (1 + a["expected_crash_pct"] / 100)  # apply crash impact

    runway = post_crash / expenses  # number of months the portfolio can sustain expenses

    return round(post_crash, 2), round(runway, 2)


# Creates a less severe crash scenario (used for comparison)
def apply_moderate_crash(portfolio):
    p = copy.deepcopy(portfolio)

    for a in p["assets"]:
        a["expected_crash_pct"] *= 0.5  # reduce crash impact by 50%

    return p


# Adjusts portfolio allocation to reduce crash damage and improve survival
def optimize_portfolio(portfolio, severity="worst"):
    p = copy.deepcopy(portfolio)

    for a in p["assets"]:
        # Measures how much this asset contributes to losses during a crash
        risk_score = abs(a["allocation_pct"] * a["expected_crash_pct"])

        threshold = 2000 if severity == "worst" else 1500  # stricter in worst-case optimization

        if risk_score > threshold:
            # Reduce allocation of assets that contribute heavily to crash losses
            a["allocation_pct"] -= (15 if severity == "worst" else 8)

        elif a["expected_crash_pct"] == 0:
            # Increase allocation to cash since it does not lose value in crash
            a["allocation_pct"] += (15 if severity == "worst" else 5)

        elif abs(a["expected_crash_pct"]) < 20:
            # Slightly increase allocation to relatively stable assets (e.g., gold)
            a["allocation_pct"] += (10 if severity == "worst" else 5)

    normalize(p)  # ensure total allocation remains 100%

    return p


# Ensures all asset allocations sum to 100%
def normalize(portfolio):
    total = sum(a["allocation_pct"] for a in portfolio["assets"])

    for a in portfolio["assets"]:
        a["allocation_pct"] = round((a["allocation_pct"] / total) * 100, 2)


# Prints reasoning behind allocation changes for transparency
def explain_changes(original, optimized):
    print("\nWHY CHANGES WERE MADE:\n")

    for orig, opt in zip(original["assets"], optimized["assets"]):
        change = round(opt["allocation_pct"] - orig["allocation_pct"], 2)

        if change == 0:
            continue  # skip assets with no change

        if change < 0:
            print(f"- Reduced {orig['name']} by {abs(change)}% -> major contributor to crash losses")

        else:
            if orig["expected_crash_pct"] == 0:
                print(f"- Increased {orig['name']} by {change}% -> improves liquidity and survival")

            elif abs(orig["expected_crash_pct"]) < 20:
                print(f"- Increased {orig['name']} by {change}% -> helps stabilize portfolio")

            else:
                print(f"- Increased {orig['name']} by {change}% -> improves diversification")


# Displays portfolio allocation as a simple bar chart
def print_bar(portfolio, title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    for a in portfolio["assets"]:
        bar = "█" * int(a["allocation_pct"] // 2)
        print(f"{a['name']:10} | {bar} ({a['allocation_pct']}%)")


# Compares survival before and after optimization for both scenarios
def compare_all(portfolio, worst_opt, mod_opt):
    print("\n" + "=" * 70)
    print("RUNWAY COMPARISON (MONTHS)")
    print("=" * 70)

    _, base_worst = compute_risk_metrics(portfolio)
    _, worst_case = compute_risk_metrics(worst_opt)

    _, base_mod = compute_risk_metrics(apply_moderate_crash(portfolio))
    _, mod_case = compute_risk_metrics(apply_moderate_crash(mod_opt))

    print(f"{'Scenario':25} | {'Current':10} | {'Optimized'}")
    print("-" * 70)
    print(f"{'Worst Case':25} | {base_worst:10} | {worst_case}")
    print(f"{'Moderate Case':25} | {base_mod:10} | {mod_case}")

    return base_worst, worst_case, base_mod, mod_case


# Converts numerical results into a simple advisor-style explanation
def explain(portfolio, worst_opt, mod_opt, stats):
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")

    base_w, opt_w, base_m, opt_m = stats

    prompt = f"""
You are a financial advisor explaining a portfolio.

Explain:
- what was risky
- what changed
- why survival improved
- what trade-off exists

Use only these assets: BTC, NIFTY50, GOLD, CASH.

Worst-case runway: {base_w} -> {opt_w}
Moderate-case runway: {base_m} -> {opt_m}

Keep it simple and conversational (5-6 sentences).
"""

    client = Groq(api_key=api_key)
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )

    return res.choices[0].message.content.strip()


if __name__ == "__main__":

    # Example portfolio (can be replaced with user input)
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

    # Optimize portfolio for extreme and moderate crash scenarios
    worst_opt = optimize_portfolio(portfolio, "worst")
    mod_opt = optimize_portfolio(portfolio, "moderate")

    # Show allocation before and after optimization
    print_bar(portfolio, "CURRENT PORTFOLIO")
    print_bar(worst_opt, "WORST-CASE OPTIMIZED")
    print_bar(mod_opt, "MODERATE-CASE OPTIMIZED")

    # Explain why allocation changes were made
    explain_changes(portfolio, worst_opt)

    # Show improvement in survival (runway)
    stats = compare_all(portfolio, worst_opt, mod_opt)

    # Final human-friendly explanation
    print("\n--- FINANCIAL ADVISOR EXPLANATION ---\n")
    print(explain(portfolio, worst_opt, mod_opt, stats))
