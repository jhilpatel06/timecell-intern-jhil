import argparse
import json
import os
from dotenv import load_dotenv
from groq import Groq


DEFAULT_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}

# --- SETUP ---------------------------------------------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")


# --- PROMPT BUILDER ------------------------------------------------------


def build_prompt(portfolio, tone):
    TONE_MAP = {
        "beginner": "simple, friendly, non-technical",
        "experienced": "clear, slightly analytical",
        "expert": "concise and insight-driven",
    }

    return f"""
You are a financial advisor speaking directly to a client analysing and providing recommendations on their investment portfolio.

Write like a short conversation - not a report.

Portfolio:
{json.dumps(portfolio, indent=2)}

Your task is to generate:
- A 3-4 sentence plain-English summary of the portfolio's risk level (focus on risk analysis)
- One specific thing the investor is doing well
- One specific thing the investor should consider changing, and why
- A one-line verdict: 'Aggressive', 'Balanced', or 'Conservative'

Use these reference criteria to judge risk:
- Crash Impact: assets with high (allocation x crash %) drive most losses
- Concentration: any single asset above ~40% increases instability
- Runway: can the portfolio survive expenses after a crash?
- Dominant Risk: which asset contributes most to downside?

Style:
- Talk directly to the user ("you")
- Be conversational and easy to follow
- Sound like a calm, supportive financial advisor
- Be empathetic but not dramatic
- Explain things as if you're helping someone understand their own money
- Tone: {TONE_MAP.get(tone, TONE_MAP["beginner"])}

Respond STRICTLY in JSON:
{{
  "summary": "...",
  "strength": "...",
  "suggestion": "...",
  "verdict": "Aggressive/Balanced/Conservative"
}}

Guidelines:
- Summary: 3-4 short sentences explaining the main risk drivers and how stable or unstable the portfolio is (no advice)
- Strength: one clear, specific positive decision
- Suggestion: one practical change, explain why the current setup is risky and what improves if changed (write naturally, no nested JSON)
- Verdict: "Aggressive/Balanced/Conservative" based on overall risk level (Aggressive = high crash impact + concentration, Conservative = low crash impact + good diversification, Balanced = in between) along with one line justification 

Keep it natural. Avoid repeating the same idea across sections.
Do not include anything outside the JSON.
"""


# --- LLM CALL ------------------------------------------------------------


def generate_portfolio_explanation(portfolio, tone="beginner"):
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")

    prompt = build_prompt(portfolio, tone)
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful and honest financial advisor.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()


# --- PARSING -------------------------------------------------------------


def parse_output(raw_output):
    try:
        return json.loads(raw_output)

    except json.JSONDecodeError:
        print("\n[WARN] JSON parsing failed. Attempting cleanup...\n")

        try:
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            cleaned = raw_output[start:end]
            return json.loads(cleaned)
        except:
            print("\n[ERROR] Failed to parse output. Raw response:\n")
            print(raw_output)
            return None


def validate_output(parsed):
    required = ["summary", "strength", "suggestion", "verdict"]
    return all(key in parsed for key in required)


def validate_critique(parsed):
    required = ["status", "issues", "improvement_hint"]
    return all(key in parsed for key in required)


def load_portfolio(path):
    if not path:
        return DEFAULT_PORTFOLIO

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an AI-powered portfolio risk explanation."
    )
    parser.add_argument(
        "--portfolio",
        help="Optional path to a JSON portfolio file. Uses the sample portfolio if omitted.",
    )
    parser.add_argument(
        "--tone",
        choices=["beginner", "experienced", "expert"],
        default="beginner",
        help="Explanation tone to request from the LLM.",
    )
    return parser.parse_args()


# --- DISPLAY -------------------------------------------------------------


def print_clean_output(parsed):
    print("\n" + "=" * 50)
    print("PORTFOLIO ANALYSIS")
    print("=" * 50)

    print("\nRisk Analysis:")
    print(parsed.get("summary", "N/A"))

    print("\nStrength:")
    print(parsed.get("strength", "N/A"))

    print("\nSuggestion:")
    print(parsed.get("suggestion", "N/A"))

    print("\nVerdict:")
    print(parsed.get("verdict", "N/A"))


def print_clean_critique(parsed):
    print("\n" + "=" * 50)
    print("CRITIQUE")
    print("=" * 50)

    print("\nStatus:")
    print(parsed.get("status", "N/A"))

    print("\nIssues:")
    issues = parsed.get("issues", [])
    if issues:
        for issue in issues:
            print(f"- {issue}")
    else:
        print("None")

    print("\nImprovement Hint:")
    print(parsed.get("improvement_hint", "N/A"))


def critique_output(raw_output):
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")

    prompt = f"""
You are reviewing a financial explanation.

Be reasonably critical, but fair. Do NOT fail for minor imperfections.

Evaluate:

1. SUMMARY:
- Short and clear (approximately 3-4 sentences)
- Explains main risk drivers
- Avoids strong advice (minor wording is okay)

2. STRENGTH:
- One clear positive
- Should be somewhat specific (not overly generic)

3. SUGGESTION:
- One actionable change
- Explains why current setup is risky
- Explains what improves after change

4. VERDICT:
- Must be Aggressive / Balanced / Conservative
- Should match reasoning

5. STYLE:
- Should feel conversational (not overly formal)
- Minor repetition is acceptable

Respond STRICTLY in JSON:

{{
  "status": "PASS" or "FAIL",
  "issues": ["only include meaningful issues"],
  "improvement_hint": "one short suggestion"
}}

Rules:
- FAIL only if there are MAJOR issues (missing structure, vague suggestion, incorrect reasoning)
- If issues are minor → still PASS
- Do NOT be overly strict

Response to review:
{raw_output}
"""

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a balanced and practical reviewer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def parse_critique(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("\n[WARN] Critique JSON parsing failed. Attempting cleanup...\n")

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            cleaned = raw[start:end]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("\n[ERROR] Failed to parse critique. Raw response:\n")
            print(raw)
            return {
                "status": "FAIL",
                "issues": ["Critique parsing failed"],
                "improvement_hint": "",
            }
    except TypeError:
        return {
            "status": "FAIL",
            "issues": ["Critique parsing failed"],
            "improvement_hint": "",
        }


# --- MAIN ---------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    portfolio = load_portfolio(args.portfolio)

    # Generate explanation
    raw = generate_portfolio_explanation(portfolio, tone=args.tone)

    # Parse response
    parsed = parse_output(raw)

    # Validate + print
    if parsed and validate_output(parsed):
        print_clean_output(parsed)
    else:
        print("\n[ERROR] Output validation failed.")

    # Critique the same response and print it in a parsed format.
    critique_raw = critique_output(raw)
    critique = parse_critique(critique_raw)

    if critique and validate_critique(critique):
        print_clean_critique(critique)
    else:
        print("\n[ERROR] Critique validation failed.")
