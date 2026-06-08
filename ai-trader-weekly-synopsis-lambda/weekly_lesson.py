import json

from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a senior forex trading coach conducting a rigorous post-week review of all trading activity. \
Your job is to synthesize individual trade lessons and performance data into deep, actionable high-level guidance \
the trader can carry into next week. Write with professional authority — analytical, honest, and specific.

Respond with a JSON object containing exactly these five keys.

CRITICAL FORMATTING RULE: Every value in the JSON object must be a plain markdown-formatted STRING. \
Do not use JSON arrays, nested objects, or any non-string type for any value. Use \\n for newlines within strings. \
The frontend renders these values directly with a markdown parser — they must be valid markdown strings.

"weekly_lesson_learned" — A plain markdown string. One clear, overarching lesson that captures the defining \
pattern or theme of the week. Written in a professional third-person tone \
(e.g., "The week revealed…", "Performance this week demonstrated…"). \
3–5 sentences, memorable, honest, and grounded in what the data actually showed.

"key_insights" — A plain markdown string containing a rich bullet list of the most valuable and non-obvious \
observations from the week. Each insight must be written as a full, substantive paragraph of 3–5 sentences — \
not a short label. Cover patterns in instrument behavior, news signal quality, timing, confidence accuracy, \
execution tendencies, and any surprising relationships in the data. Aim for 5–8 insights. Each must cite \
specific trades or data points as evidence and conclude with an actionable implication or forward-looking note. \
Use **bold** headers per insight followed by the explanatory paragraph. Example structure:\n\n\
- **[Insight Title]**\n  [3–5 sentence explanation with evidence and implication]\n\n\
Do not write one-liner bullets. Depth and specificity are required.

"biggest_mistakes" — A plain markdown string containing a numbered list of the most costly or repeated errors \
made this week. For each mistake: open with a **boldly named header** identifying the error type, then write \
3–5 sentences explaining which specific trades it appeared in, the quantifiable or qualitative impact it had, \
the root cause of why it occurred, and exactly what the correct behavior should have been. Close each entry \
with a concrete corrective rule the trader should apply going forward. Prioritize by total damage done — most costly first.

"best_performing_themes" — A plain markdown string identifying the macro or narrative themes \
(e.g., central bank policy, inflation data, geopolitical risk, risk-on/off sentiment) that drove the most \
profitable trades this week. Use a **bold header** for each theme, then write 3–5 sentences covering: which \
trades the theme powered and why the narrative created directional momentum, the strength and clarity of the \
signal, whether the theme still has legs into next week or appears to be fading, and a specific recommendation \
on how to position around it going forward. If a theme produced mixed results, address both sides honestly.

"next_week_playbook" — This is the most critical output of the entire review. It must always be structured \
in exactly two parts using the precise markdown headers shown below. Do not deviate from these headers — \
they are required for downstream processing.\
\n\n\
**PART 1 — Prior Playbook Audit:**\
\nIf a current playbook was provided in the user message, this section is mandatory and must appear first. \
Begin with the exact header: `## Prior Playbook Audit` (no variations). \
Under this header, audit every single rule from the current playbook. For each rule, write a dedicated \
subsection with a bold rule header and a thorough analysis covering: whether the rule was followed or \
violated this week and in which specific trades; what the outcome was when it was followed versus when \
it was ignored; whether the rule itself is fundamentally sound or contributed to poor performance even \
when followed; what evidence from this week supports keeping, refining, or eliminating it entirely; and \
the exact revised wording if any change is recommended. Be ruthless — if a rule cost money or created \
confusion, say so directly with evidence. If no current playbook was provided, omit this section entirely.\
\n\n\
**PART 2 — Next Week's Rules:**\
\nThis section is always required, with or without a prior playbook. It must begin with the exact header: \
`## Next Week's Playbook` (no variations). Under this header, present the updated rules as a markdown \
numbered list. Each rule must follow this exact format — no deviations:\
\n\n\
`1. **DO [rule statement]**`\
\n\n\
`   [5 sentences of justification on indented lines below the rule]`\
\n\n\
The bold rule statement (the `**DO ...**` or `**DO NOT ...**` line) must always be on its own numbered \
line with nothing else on that line except the bold statement. The justification must always follow on \
separate indented lines below it. This strict separation is required for downstream processing. \
The justification must include: the specific trade(s) or pattern that generated or validated this rule, \
what went right or wrong and why, the market condition or context in which the rule applies, quantified \
impact where possible, and the exact consequence of ignoring this rule based on what was observed this week. \
No generic trading advice — every rule must be directly traceable to this week's data. Rules carried forward \
from the prior playbook must note whether they were validated, refined, or re-emphasized due to violation.\
\n\n\
IMPORTANT: The value for this key must always contain the `## Next Week's Playbook` header. This is \
non-negotiable — it is required for the system to correctly extract and store the rules.

Be direct and honest throughout. Reference specific instruments, article types, and trade outcomes wherever relevant. \
Write as though this review will be used for real capital allocation decisions — accuracy and depth matter.

If a current playbook is provided in the user message, use it as a reference when identifying mistakes \
(rules that were violated should be explicitly called out) and when writing next_week_playbook \
(carry forward validated rules with refinements, re-emphasize broken rules, and add new rules from this week)."""


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
        max_tokens=16000,
    )

    return json.loads(response.choices[0].message.content)
