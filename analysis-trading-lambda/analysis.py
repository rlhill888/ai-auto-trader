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
