import copy
import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------- RISK ---------------- #

def compute_risk_metrics(portfolio):
    total = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]

    post_crash = 0
    for a in portfolio["assets"]:
        val = total * a["allocation_pct"] / 100
        post_crash += val * (1 + a["expected_crash_pct"] / 100)

    runway = post_crash / expenses
    return round(post_crash, 2), round(runway, 2)


def apply_moderate_crash(portfolio):
    p = copy.deepcopy(portfolio)
    for a in p["assets"]:
        a["expected_crash_pct"] *= 0.5
    return p


# ---------------- OPTIMIZERS ---------------- #

def optimize_worst_case(portfolio):
    p = copy.deepcopy(portfolio)

    for a in p["assets"]:
        risk = abs(a["allocation_pct"] * a["expected_crash_pct"])

        if risk > 2000:
            a["allocation_pct"] -= 15
        elif a["expected_crash_pct"] == 0:
            a["allocation_pct"] += 15
        elif abs(a["expected_crash_pct"]) < 20:
            a["allocation_pct"] += 10

    normalize(p)
    return p


def optimize_moderate_case(portfolio):
    p = copy.deepcopy(portfolio)

    for a in p["assets"]:
        risk = abs(a["allocation_pct"] * a["expected_crash_pct"])

        if risk > 2000:
            a["allocation_pct"] -= 8
        elif a["expected_crash_pct"] == 0:
            a["allocation_pct"] += 5
        elif abs(a["expected_crash_pct"]) < 20:
            a["allocation_pct"] += 5

    normalize(p)
    return p


def normalize(portfolio):
    total = sum(a["allocation_pct"] for a in portfolio["assets"])
    for a in portfolio["assets"]:
        a["allocation_pct"] = round((a["allocation_pct"] / total) * 100, 2)


# ---------------- CLI VISUAL ---------------- #

def print_bar(portfolio, title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    for a in portfolio["assets"]:
        bar = "█" * int(a["allocation_pct"] // 2)
        print(f"{a['name']:10} | {bar} ({a['allocation_pct']}%)")


# ---------------- SCENARIO METRICS ---------------- #

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


# ---------------- LLM ---------------- #

def explain(portfolio, worst_opt, mod_opt, stats):
    base_w, opt_w, base_m, opt_m = stats

    prompt = f"""
You are a financial advisor talking to a client.

Explain their portfolio in a friendly, simple way.

Include SOME numbers to help them understand, but keep it easy.

Data:

Current worst-case runway: {base_w} months
Optimized worst-case runway: {opt_w} months

Current moderate-case runway: {base_m} months
Optimized moderate-case runway: {opt_m} months

Instructions:
- Talk like a human, not a report
- Explain what was risky
- Explain what changed
- Mention improvement in runway
- Keep it reassuring

Limit to 5-6 sentences
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )

    return res.choices[0].message.content.strip()


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

    worst_opt = optimize_worst_case(portfolio)
    mod_opt = optimize_moderate_case(portfolio)

    print_bar(portfolio, "CURRENT PORTFOLIO")
    print_bar(worst_opt, "WORST-CASE OPTIMIZED")
    print_bar(mod_opt, "MODERATE-CASE OPTIMIZED")

    stats = compare_all(portfolio, worst_opt, mod_opt)

    print("\n--- FINANCIAL ADVISOR EXPLANATION ---\n")
    print(explain(portfolio, worst_opt, mod_opt, stats))