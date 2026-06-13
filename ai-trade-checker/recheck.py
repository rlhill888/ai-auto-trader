import json

from openai import OpenAI

from config import OPENAI_API_KEY
from dynamodb import get_current_playbook

openai_client = OpenAI(api_key=OPENAI_API_KEY)

RECHECK_SYSTEM_PROMPT = """You are a forex trading risk manager reviewing a live open trade. Given the original trade rationale and its current live state (unrealized P&L, time elapsed since entry), decide whether to stay in the trade or exit now.

Consider: whether the original thesis is still valid, what the current unrealized P&L suggests about momentum, how much time has passed relative to the estimated trade timeframe, and whether the risk/reward still justifies staying in.

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{
  "should_stay": true or false,
  "reason": "3-5 sentence explanation covering: whether the original thesis still holds, what the current P&L and market state suggest, any changed conditions that support staying or exiting, and why this decision was made"
}"""


def analyze_trade_recheck(trade: dict, oanda_trade: dict) -> dict:
    playbook = get_current_playbook()
    system_prompt = RECHECK_SYSTEM_PROMPT
    if playbook:
        system_prompt += f"\n\nMake sure the following rules are followed: \n\n=== RULES FOR TRADE ===\n{playbook}"
    unrealized_pl = oanda_trade.get("unrealizedPL", "N/A")
    current_units = oanda_trade.get("currentUnits", "N/A")
    open_time = oanda_trade.get("openTime", "N/A")

    user_message = (
        f"=== ORIGINAL TRADE ===\n"
        f"Instrument: {trade.get('instrument')}\n"
        f"Direction: {trade.get('direction')}\n"
        f"Confidence: {trade.get('confidence')}\n"
        f"Confidence duration: {trade.get('confidence_duration')}\n"
        f"Estimated trade timeframe: {trade.get('estimated_trade_timeframe')}\n"
        f"Original reasoning: {trade.get('reasoning')}\n"
        f"Article title: {trade.get('article_title')}\n"
        f"Article summary: {trade.get('article_summary')}\n"
        f"Trade opened at: {trade.get('timestamp')}\n"
        f"Last rechecked at: {trade.get('trade_last_checked') or 'Never (first recheck)'}\n\n"
        f"=== CURRENT LIVE STATE ===\n"
        f"Unrealized P&L: {unrealized_pl}\n"
        f"Current units: {current_units}\n"
        f"OANDA open time: {open_time}\n\n"
        f"Should we stay in this trade or exit now?"
    )

    response = openai_client.chat.completions.create(
        model="gpt-5.5-2026-04-23",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
