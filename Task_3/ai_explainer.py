import json
import os
from dotenv import load_dotenv
from groq import Groq

# Load env
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_portfolio_explanation(portfolio, tone="beginner"):
    prompt = f"""
You are a financial advisor explaining portfolio risk to a non-expert client.

Your job is NOT to repeat the numbers. Your job is to INTERPRET them.

Portfolio:
{json.dumps(portfolio, indent=2)}

Think about:
- crash impact (which assets hurt most)
- concentration risk
- stability vs volatility
- ability to survive expenses (runway mindset)

Respond STRICTLY in this JSON format:
{{
  "summary": "...",
  "strength": "...",
  "suggestion": "...",
  "verdict": "Aggressive/Balanced/Conservative"
}}

Guidelines:

SUMMARY:
- 3–4 sentences
- Explain overall risk level in simple terms
- Mention key drivers of risk (e.g. high crypto exposure)

STRENGTH:
- Identify ONE genuinely good thing about the portfolio
- Be specific (not generic like "diversified")

SUGGESTION:
- Give ONE clear, actionable improvement
- Explain WHY it matters

VERDICT RULES:
- Aggressive → high volatility / high crash exposure
- Balanced → mix of risk and stability
- Conservative → mostly stable assets

TONE:
- Friendly, clear, non-technical
- Honest but not harsh
- Speak like advising a real client

IMPORTANT:
- Do NOT repeat raw numbers unnecessarily
- Do NOT include anything outside JSON
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful financial advisor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def parse_output(raw_output):
    try:
        return json.loads(raw_output)

    except json.JSONDecodeError:
        print("\n⚠️ JSON parsing failed. Attempting cleanup...\n")

        try:
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            cleaned = raw_output[start:end]
            return json.loads(cleaned)
        except:
            print("\n❌ Still failed to parse. Raw output:\n")
            print(raw_output)
            return None


def print_clean_output(parsed):
    print("\n" + "=" * 50)
    print("PORTFOLIO ANALYSIS")
    print("=" * 50)

    print("\nSummary:")
    print(parsed.get("summary", "N/A"))

    print("\nStrength:")
    print(parsed.get("strength", "N/A"))

    print("\nSuggestion:")
    print(parsed.get("suggestion", "N/A"))

    print("\nVerdict:")
    print(parsed.get("verdict", "N/A"))


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
        ],
    }

    raw = generate_portfolio_explanation(portfolio)

    print("\n--- RAW LLM OUTPUT ---\n")
    print(raw)

    parsed = parse_output(raw)

    if parsed:
        print_clean_output(parsed)
