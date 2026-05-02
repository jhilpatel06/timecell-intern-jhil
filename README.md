# timecell-intern-jhil

## Overview

This project works through evaluating a portfolio under a crash scenario, bringing in live market data, and generating a plain-English explanation of the risk.

Since finance was not a familiar domain, the initial effort went into understanding how allocation, crash assumptions, and expenses translate into actual outcomes like portfolio survival. Once that was clear, the focus shifted to building a working version and improving how the results are interpreted.

AI tools were used to speed up development and iterate on different approaches, while the direction, validation, and refinements were guided by observing where the outputs felt unclear or incomplete.

Overall, the process remained incremental — starting simple and refining based on what was missing or not working well.

---

## Tech Stack

- Python 3.10+ — used for implementing the core logic, data handling, and CLI output.

- yfinance — used to fetch market data for index, gold, and currency conversion inputs.

- pycoingecko — used to fetch live crypto prices without requiring API setup.

- tabulate — used to present results in a structured and readable table format in the terminal.

- python-dotenv — used to manage API keys through a local `.env` file.

- Gemini API — used as the first-choice LLM for generating portfolio explanations.

- Groq API (llama-3.1-8b-instant) — used as the fallback generator and as the critique model for validation.

## Project Structure

```text
timecell-intern-jhil/
│
├── Task_1/
│   └── portfolio_risk_calculator.py   # crash simulation, runway, risk metrics
│
├── Task_2/
│   └── market_fetch.py                # live data (crypto, index, gold)
│
├── Task_3/
│   └── ai_explainer.py                # LLM prompt, parsing, validation, critique
│
├── Task_4/
│   └── suggestor.py                  # allocation adjustments and comparison
│
├── requirements.txt                  # dependencies
└── README.md                         # documentation
```

Install dependencies:

```bash
pip install -r requirements.txt
```

For Tasks 3 and 4, add a `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_api_key_here
```

---

## Task 1

### What was given

This was a portfolio risk calculation problem where the main challenge was converting allocations and crash assumptions into meaningful financial outcomes.

### How I approached it

- Allocation percentages were converted into actual asset values using  
  `asset_value = total_value × allocation_pct / 100`

- The expected crash percentage was applied to each asset independently as  
  `post_crash_asset = asset_value × (1 + crash_pct / 100)`

- The post-crash values were aggregated to compute the total portfolio value after a crash.

- Monthly expenses were used to estimate runway:  
  `runway = post_crash_value / monthly_expenses`

- Risk contribution was evaluated using  
  `risk_score = allocation_pct × |crash_pct|`  
  to identify the asset contributing most to downside.

- Required validations such as handling zero expenses and invalid allocations were included.

- Both severe and moderate crash scenarios were considered to provide additional context.

### Final outcome

The solution provides post-crash value, runway, ruin test status, largest risk contributor, and allocation concentration in a clear and interpretable form. It also flags concentration risk when any single asset is more than 40% of the portfolio.

---
## Task 2

### What was given

This task moved the project from static assumptions to live market data.

### How I approached it

- CoinGecko was used for crypto prices.
- Yahoo Finance was used for index prices, gold pricing, and USD-INR conversion.
- Each asset fetch was handled independently to avoid coupling failures.
- The output was structured as a table to keep the results easy to scan and compare.

### Key considerations

- External APIs are not always reliable, so failures should not break the entire pipeline.
- Gold pricing required a realistic conversion from global market units rather than fixed assumptions.
- Static values were insufficient for a system intended to reflect live market conditions.

### What was implemented

- Error handling around each fetch to isolate failures and allow partial results.
- Conversion of gold prices from USD per ounce to INR per gram using USD-INR.
- Consistent formatting of output to maintain readability even when some data is unavailable.

### Final outcome

The system fetches live crypto, index, and gold prices, handles failures gracefully, and presents the results in a consistent and readable format.

---

## Task 3

### What was given

This task required generating a plain-English explanation of the portfolio using an LLM.

### How I approached it

- A basic prompt was used initially to pass portfolio details to the model.
- The Gemini API was used first for response generation, with Groq as a fallback if Gemini is unavailable or fails.
- The implementation was structured into separate steps for prompt building, API calling, output parsing, and validation.

### What didn't work initially

- The initial outputs were generic and repetitive.
- Explanations often included advice without clearly explaining the reasoning.
- The tone was not always aligned with a non-finance user.

### What I changed

- A fixed response structure was introduced: summary, strength, suggestion, and verdict.
- The prompt was refined to ensure the model explains why a particular allocation is risky.
- The tone was adjusted to make the explanation more conversational and practical.
- Parsing and validation were added to ensure the response follows the expected structure.
- The script prints both the raw LLM response and the extracted structured output separately.

### Additional step

- A second LLM call using Groq was introduced to critique the generated explanation.
- This helped evaluate clarity, structure, and usefulness instead of relying only on the initial output and could be used as feedback to refine the prompt further.

### Final outcome

The explanations became more consistent, clearer, and more useful, with structured outputs and an additional validation step improving reliability.

---

## Task 4

### Problem chosen

Given a portfolio and its risk analysis under crash scenarios, determine how the asset allocation can be adjusted to improve resilience, and quantify the impact of those changes.

### Why this problem

The existing system explains the current portfolio but does not indicate what can be changed. Extending it to suggest and evaluate allocation changes connects analysis with actionable decision-making.

This also connects with Timecell's product direction, where portfolio risk metrics are not only calculated but used to surface intelligent recommendations for wealth management decisions.

### How it was implemented

- Existing risk calculations were used to identify assets contributing most to downside.
- Allocation adjustments were made based on risk contribution.
- Adjusted allocations were normalized to ensure the portfolio remains valid.
- Both original and adjusted portfolios were evaluated under severe and moderate crash scenarios.
- The final explanation uses Gemini first and falls back to Groq if Gemini is unavailable.

### What this adds

- A clear before-and-after comparison instead of only describing the current state.
- Visibility into how allocation changes affect post-crash value and runway.
- An explanation layer that connects the changes to their impact.

### Final outcome

The system now extends beyond analysis and provides a simple, interpretable way to explore how allocation changes can improve portfolio stability.

---

## How AI tools were used

### Where AI helped

- ChatGPT was used to understand unfamiliar finance concepts and break the assignment into smaller parts.
- Codex and Copilot were used to generate early code drafts and accelerate implementation.
- AI was used most heavily when iterating on prompt structure for Task 3.

### How it was controlled

- Generated code was reviewed manually instead of being accepted directly.
- Scripts were tested and refined based on actual outputs.
- Smaller, targeted prompts were used for improvements instead of regenerating full solutions.

### Where iteration mattered most

- Task 3 required the most iteration, as prompt quality directly affected the usefulness of the explanation.
- Better results came from gradually refining structure, tone, and validation rather than relying on a single prompt.

---

## Hardest Part

Task 3 was the most challenging, as the initial LLM outputs were generic and inconsistent. The difficulty was not generating responses, but making them structured, clear, and useful. This was addressed by refining the prompt, adding parsing and validation, and introducing a critique step to improve consistency.

---

## Key Learnings

- Understanding the domain first made the implementation easier to reason about.
- Numerical correctness alone is not sufficient without clear interpretation of results.
- API-based systems require graceful failure handling due to unreliable external data.
- LLM outputs improve significantly when structure, tone, and reasoning are explicitly defined.
- Iterative refinement of generated code and prompts is more effective than one-shot generation.

---

## How to Run

```bash
python Task_1/portfolio_risk_calculator.py
python Task_2/market_fetch.py
python Task_3/ai_explainer.py
python Task_4/suggestor.py
```
