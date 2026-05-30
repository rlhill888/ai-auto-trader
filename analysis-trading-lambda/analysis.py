import json

from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a forex trading analyst. Given a financial news article, analyze whether it presents a clear trading opportunity in the forex market.

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
- Only recommend a trade if confidence is above 0.65"""


def analyze_article(article: dict) -> dict:
    title = article.get("title", "")
    summary = article.get("summary", "")
    user_message = f"Title: {title}\n\nSummary: {summary}"

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
    print(f"OpenAI response: {raw}")
    analysis = json.loads(raw)

    if analysis.get("confidence", 0) < 0.65:
        analysis["is_good_trade"] = False

    return analysis
