import json

from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a forex trading analyst. Given a financial news article, analyze whether it presents a clear trading opportunity in the forex market.

Each trade uses a 1:2 risk/reward structure — a 20-pip stop loss and a 40-pip take profit. The trade risks 0.5% of the account to potentially gain 1.0%. Only recommend a trade if the news signal gives the price a realistic chance of moving 40 pips in the expected direction before hitting the 20-pip stop. A weak or ambiguous signal is not worth the risk — the take profit is twice as far as the stop loss, so the directional conviction must be high.

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{
  "is_good_trade": true or false,
  "instrument": "EUR_USD",
  "direction": "buy" or "sell",
  "reasoning": "brief explanation of your decision",
  "confidence": 0.85
}

Rules:
- instrument must be a valid OANDA forex pair like EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, etc.
- confidence must be a float between 0.0 and 1.0
- If no clear trade exists, set is_good_trade to false; other fields can still be filled with best guesses
- Only recommend a trade if confidence is above 0.65
- Ask yourself: is this signal strong enough that price is more likely to reach +40 pips than -20 pips?"""


EARLY_EXIT_SYSTEM_PROMPT = """You are a forex trading risk manager. An open trade exists, and new analysis with high confidence suggests the market will move in the OPPOSITE direction. Evaluate whether the existing trade should be closed early to limit losses or lock in profits, and whether a new trade in the opposite direction should be opened.

Consider: the confidence levels of both analyses, the quality of reasoning for each, and whether the new signal is strong enough to justify the cost of reversing (spread + any current loss on the open trade).

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{
  "should_exit": true or false,
  "reason": "brief explanation of your decision"
}"""


def analyze_early_exit(current_trade: dict, new_analysis: dict, new_article: dict) -> dict:
    current_direction = current_trade.get("direction", "")
    new_direction = new_analysis.get("direction", "")
    user_message = (
        f"=== CURRENT OPEN TRADE ===\n"
        f"Direction: {current_direction}\n"
        f"Original confidence: {current_trade.get('confidence', 0):.2f}\n"
        f"Original reasoning: {current_trade.get('reasoning', '')}\n"
        f"Original article title: {current_trade.get('article_title', '')}\n"
        f"Original article summary: {current_trade.get('article_summary', '')}\n\n"
        f"=== NEW OPPOSING SIGNAL ===\n"
        f"New article title: {new_article.get('title', '')}\n"
        f"New article summary: {new_article.get('summary', '')}\n"
        f"Suggested direction: {new_direction} (OPPOSITE to current {current_direction})\n"
        f"New confidence: {new_analysis.get('confidence', 0):.2f}\n"
        f"New reasoning: {new_analysis.get('reasoning', '')}\n\n"
        f"Should the current {current_direction} trade be closed early and a new {new_direction} trade opened instead?"
    )

    print(f"Sending early exit analysis to OpenAI | current={current_direction} new={new_direction}")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EARLY_EXIT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    print(f"Early exit analysis response: {raw}")
    return json.loads(raw)


def analyze_article(article: dict, risk_amount: float) -> dict:
    title = article.get("title", "")
    summary = article.get("summary", "")
    reward_amount = round(risk_amount * 2, 2)
    user_message = (
        f"Title: {title}\n\n"
        f"Summary: {summary}\n\n"
        f"Risk/reward context: This trade risks ${risk_amount:.2f} (20-pip stop loss) to potentially gain ${reward_amount:.2f} (40-pip take profit). "
        f"Is the news signal strong enough that price is more likely to hit +40 pips than -20 pips?"
    )

    print(f"Sending article to OpenAI for analysis: {title}")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    print(f"OpenAI response: {raw}")
    analysis = json.loads(raw)

    if analysis.get("confidence", 0) < 0.65:
        analysis["is_good_trade"] = False

    return analysis
