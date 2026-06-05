from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a forex trading coach reviewing completed trades. Given the details of a closed trade, write a concise lesson learned (2-4 sentences) that explains what worked, what didn't, and what should be done differently next time. Focus on actionable insights based on the trade outcome relative to the original reasoning and confidence level. If the trade was exited early, acknowledge that directly and factor the reason into the lesson."""


def generate_lesson_learned(trade: dict, exit_price: float, profit_loss: float, left_trade_early: bool = False, early_exit_reason: str = None) -> str:
    outcome = "profitable" if profit_loss > 0 else "a loss"
    user_message = (
        f"Instrument: {trade.get('instrument')}\n"
        f"Direction: {trade.get('direction')}\n"
        f"Confidence: {trade.get('confidence')}\n"
        f"Article title: {trade.get('article_title')}\n"
        f"Article summary: {trade.get('article_summary')}\n"
        f"Original reasoning: {trade.get('reasoning')}\n"
        f"Exit price: {exit_price}\n"
        f"Profit/loss (account currency): {profit_loss}\n"
        f"Outcome: {outcome}\n"
        f"Exited early: {'yes' if left_trade_early else 'no'}\n"
        + (f"Reason for early exit: {early_exit_reason}\n" if left_trade_early and early_exit_reason else "")
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()
