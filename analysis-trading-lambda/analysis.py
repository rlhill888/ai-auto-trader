import json
from datetime import datetime, timezone

from openai import OpenAI

from config import OPENAI_API_KEY
from dynamodb import get_current_playbook

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a forex trading analyst. Given a financial news article, analyze whether it presents a clear trading opportunity in the forex market.

The trade risks 0.5% of the account — position size is calculated automatically to match whatever stop loss you choose. Choose stop_loss_pips and take_profit_pips based on the strength, clarity, and expected volatility of the news signal.

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{
  "is_good_trade": true or false,
  "instrument": "EUR_USD",
  "direction": "buy" or "sell",
  "reasoning": "3-5 sentence explanation covering: what the news signal is, why it favors this direction and instrument, key risks to the trade, and why the chosen stop/take-profit levels suit this signal",
  "confidence": 0.85,
  "stop_loss_pips": 20,
  "take_profit_pips": 40,
  "confidence_duration": "8 hours",
  "estimated_trade_timeframe": "4-8 hours",
  "recheck_duration": "2 hours",
  "estimated_latest_trade_end": "2026-06-07T18:00:00Z"
}

Rules:
- instrument must be a valid OANDA forex pair (EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, etc.)
- confidence must be a float between 0.0 and 1.0
- stop_loss_pips: 10–80. Use tighter stops (10–20) for precise high-confidence signals, wider (25–80) for volatile or uncertain moves
- take_profit_pips: minimum 1.5× stop_loss_pips. Use higher multiples (2×–4×) for strong, clear signals
- Only recommend a trade if confidence is above 0.65
- If is_good_trade is false, still return 20 / 40 as defaults for the pip fields
- confidence_duration: how long the confidence rating should be trusted based on the news type (e.g. "4 hours", "2 days")
- estimated_trade_timeframe: how long the trade is expected to run before hitting TP/SL (e.g. "1-2 hours", "3 days")
- recheck_duration: how often the system should recheck this live trade — must be in the format "N unit" where unit is one of: minutes, hours, days, weeks (e.g. "30 minutes", "2 hours", "1 day") — use shorter intervals for fast-moving news, longer for slow macro signals
- All three duration fields are required even when is_good_trade is false; use sensible defaults like "24 hours" in that case
- estimated_latest_trade_end: an ISO 8601 UTC timestamp (e.g. "2026-06-07T18:00:00Z") representing the absolute latest you expect this trade to still be running, calculated from the current time provided in the prompt; use the upper bound of your estimated_trade_timeframe"""


EARLY_EXIT_SYSTEM_PROMPT = """You are a forex trading risk manager. An open trade exists, and new analysis with high confidence suggests the market will move in the OPPOSITE direction. Evaluate whether the existing trade should be closed early to limit losses or lock in profits, and whether a new trade in the opposite direction should be opened.

Consider: the confidence levels of both analyses, the quality of reasoning for each, and whether the new signal is strong enough to justify the cost of reversing (spread + any current loss on the open trade).

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{
  "should_exit": true or false,
  "reason": "3-5 sentence explanation covering: why the new signal contradicts the existing trade, the relative strength of both signals, what risk is being avoided or locked in by exiting, and why this decision was made over staying in the trade"
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
        max_tokens=500,
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
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    playbook = get_current_playbook()
    system_prompt = SYSTEM_PROMPT
    if playbook:
        system_prompt += f"\n\n=== RULES FOR TRADE ===\n{playbook}"
    user_message = (
        f"Current UTC time: {current_time}\n\n"
        f"Title: {title}\n\n"
        f"Summary: {summary}\n\n"
        f"Risk context: This trade risks ${risk_amount:.2f} (0.5% of account). "
        f"Choose stop_loss_pips and take_profit_pips that suit the signal strength and expected volatility."
    )

    print(f"Sending article to OpenAI for analysis: {title}")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=500,
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

    analysis["stop_loss_pips"] = int(analysis.get("stop_loss_pips", 20))
    analysis["take_profit_pips"] = int(analysis.get("take_profit_pips", 40))

    return analysis
