import json

from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a senior forex trading coach reviewing a full week of trading activity. \
Your job is to synthesize the individual trade lessons into high-level guidance the trader can carry into next week.

Respond with a JSON object containing exactly these five keys:

"weekly_lesson_learned" — One clear, overarching lesson from the week as a whole. Identify the theme or pattern \
that most defined the week's results. Write it as a direct, memorable takeaway (2–4 sentences). Use markdown.

"key_insights" — A markdown bullet list of the most valuable observations from the week. These are the sharp, \
non-obvious things worth remembering — patterns in instrument behavior, news signal quality, confidence accuracy, \
or anything else that stands out. Aim for 4–7 insights. Each should be specific and grounded in the data.

"biggest_mistakes" — A markdown numbered list of the most costly or repeated errors. For each mistake: name it \
boldly, explain which trade(s) it appeared in and the impact, and state what the correct behavior should have been. \
Prioritize by damage done.

"best_performing_themes" — A markdown section identifying the macro or narrative themes (e.g. central bank policy, \
inflation data, geopolitical risk, risk-on/off sentiment) that drove the most profitable trades this week. For each \
theme: name it, explain which trades it powered, and note whether it still has legs going into next week or appears \
to be fading.

"next_week_playbook" — A markdown numbered checklist of concrete, actionable rules for next week derived directly \
from this week's trades. Frame them as DO or DO NOT statements. No generic advice.

Be direct and honest. Reference specific instruments, article types, or patterns where relevant.

If a current playbook is provided in the user message, use it as a reference when identifying mistakes \
(rules that were violated should be highlighted) and when writing next_week_playbook \
(validated rules can be refined, violated rules re-emphasized, and new rules added from this week's findings)."""


def _format_trade_lesson(index: int, trade: dict) -> str:
    lesson = trade.get("lesson_learned") or "No lesson recorded."
    return (
        f"Trade {index} — {trade.get('instrument')} {trade.get('direction')} "
        f"({'WIN' if trade.get('is_successful') else 'LOSS'}, P&L: {trade.get('profit_loss')}):\n"
        f"  Article: {trade.get('article_title')}\n"
        f"  Reasoning: {trade.get('reasoning')}\n"
        f"  Exited early: {trade.get('left_trade_early')}\n"
        f"  Early exit reason: {trade.get('reason_for_leaving_trade_early')}\n"
        f"  Lesson learned: {lesson}\n"
    )


def generate_weekly_lesson(trades: list[dict], week_start, week_end, synopsis: str = None, current_playbook: str = None) -> dict:
    trades_with_lessons = [t for t in trades if t.get("lesson_learned")]

    if not trades:
        return {
            "weekly_lesson_learned": "No closed trades were recorded this week.",
            "key_insights": None,
            "biggest_mistakes": None,
            "best_performing_themes": None,
            "next_week_playbook": None,
        }

    if not trades_with_lessons:
        return {
            "weekly_lesson_learned": "No individual lessons were recorded for trades this week.",
            "key_insights": None,
            "biggest_mistakes": None,
            "best_performing_themes": None,
            "next_week_playbook": None,
        }

    trades_text = "\n".join(_format_trade_lesson(i + 1, t) for i, t in enumerate(trades))
    playbook_section = f"Current playbook:\n\n{current_playbook}\n\n" if current_playbook else ""
    synopsis_section = f"Weekly synopsis:\n\n{synopsis}\n\n" if synopsis else ""
    user_message = (
        f"Week: {week_start} to {week_end}\n"
        f"Total closed trades: {len(trades)}\n"
        f"Trades with lessons recorded: {len(trades_with_lessons)}\n\n"
        f"{playbook_section}"
        f"{synopsis_section}"
        f"Trade data:\n\n{trades_text}"
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.5,
        max_tokens=4000,
    )

    return json.loads(response.choices[0].message.content)
