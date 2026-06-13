from openai import OpenAI

from config import OPENAI_API_KEY
from dynamodb import get_current_playbook

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a forex trading coach reviewing completed trades. Given the details of a closed trade, write a detailed lesson learned (4-6 sentences) covering: whether the original reasoning held up against the outcome, what the news signal got right or wrong, how the confidence level reflected the actual result, what the stop loss and take profit placement suggests about the trade setup, and one specific actionable takeaway for future trades of this type. If the trade was exited early, acknowledge that directly and factor the reason into the lesson."""


def generate_lesson_learned(trade: dict, exit_price: float, profit_loss: float, left_trade_early: bool = False, early_exit_reason: str = None) -> str:
    playbook = get_current_playbook()
    system_prompt = SYSTEM_PROMPT
    if playbook:
        system_prompt += f"\n\n=== RULES FOR TRADE ===\n{playbook}"
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
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=2000,
    )

    return response.choices[0].message.content.strip()
