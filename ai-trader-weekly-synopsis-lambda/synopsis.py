from openai import OpenAI

from config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def _build_system_prompt(base_url: str, current_playbook: str = None) -> str:
    example_url = f"{base_url}/trades/abc-123" if base_url else "/trades/abc-123"
    playbook_section = """

### This Week's Playbook
List the exact rules from the current playbook (provided in the user message) that the trader was following this week. \
Display them as a numbered list so the reader knows exactly what the rules were going in.

### Playbook Analysis
For each rule in the playbook, answer three things:
1. **Followed?** — Did the trades honor it, violate it, or was it untested this week? Reference specific trades.
2. **Did it work?** — When the rule was followed, did it produce better outcomes? Was the rule itself sound given what actually happened this week? Could the rule itself have been the problem — did following it hurt performance?
3. **Keep, change, or drop?** — Should this rule stay as-is, be refined, or be removed entirely? If it needs changing, suggest the revised version directly.

Be direct and honest. If a rule was flawed or counterproductive, call it out clearly.""" if current_playbook else ""
    return f"""You are an expert forex trading analyst and coach generating a weekly trading synopsis. \
Analyze the trade data provided and produce an engaging, insightful report formatted in markdown.

Structure the report exactly as follows:

1. **Weekly Performance Summary** — Open with a recap of the week: total trades, win rate, net P&L, standout moments.

2. Then answer each question below, organized under their section headers. Be specific and reference actual trades where relevant. If the data is insufficient to answer a question, say so briefly.

---

### Edge Discovery
- Which trade setups generated the highest expectancy?
- Which article categories produced the largest average moves?
- Which trades had the highest win rate?
- Which trades had the best risk-to-reward ratio?
- Which currencies performed best?
- Which currency pairs should I trade more often?
- Which trade types should I eliminate?
- Which catalysts consistently created follow-through?
- Which catalysts created fakeouts?

### Timing Analysis
- Did entering immediately after publication outperform waiting?
- What entry timing produced the best results?
- How long after publication does market reaction typically peak?
- Which time of day generated the best trades?
- Which trading sessions were most profitable?
- Which day of the week performed best?
- Which day of the week should be avoided?

### News Source Analysis
- Which publication generated the most profitable signals?
- Which publication generated the most losing trades?
- Which authors produced the highest-quality signals?
- Which sources consistently report information too late?
- Which sources tend to publish market-moving information earliest?
- Which sources create the most noise?
- Which sources should be removed from my watchlist?

### Market Environment Analysis
- What market conditions existed during my best trades?
- What market conditions existed during my worst trades?
- Was volatility helping or hurting me?
- Did trending markets outperform range-bound markets?
- Did high-impact news weeks help performance?
- Was I more successful during risk-on or risk-off environments?
- Which macro themes dominated profitable trades?

### Execution Analysis
- Did I follow my trading plan?
- Which rules did I break most often?
- What execution mistakes repeated?
- How much profit was lost due to poor entries?
- How much profit was lost due to poor exits?
- Was I moving stops too early?
- Was I taking profits too early?
- Which losing trades were actually good trades?
- Which winning trades were actually bad trades?

### Best Performing Themes
Identify the macro or narrative themes (e.g. central bank policy, inflation data, geopolitical risk, risk-on/off sentiment) \
that drove the most profitable trades this week. For each theme: name it, explain which trades it powered, and rate \
whether it still has legs going into next week or appears to be fading.

---

Use markdown headers, bullet points, bold text, and tables where they add clarity. Be honest and specific.

When referencing a specific trade, format its name as a markdown link using the URL provided in the trade data. \
Example: [EUR_USD BUY]({example_url}). Always use the trade's link_url field for this.{playbook_section}"""


def _format_trade(index: int, trade: dict, base_url: str) -> str:
    trade_id = trade.get("trade_id", "")
    link_url = f"{base_url}/trades/{trade_id}" if base_url and trade_id else ""
    return (
        f"Trade {index}:\n"
        f"  Trade ID: {trade_id}\n"
        f"  Link URL: {link_url}\n"
        f"  Instrument: {trade.get('instrument')}\n"
        f"  Direction: {trade.get('direction')}\n"
        f"  Opened at: {trade.get('timestamp')}\n"
        f"  Closed at: {trade.get('closed_at')}\n"
        f"  Profit/Loss: {trade.get('profit_loss')}\n"
        f"  Successful: {trade.get('is_successful')}\n"
        f"  Confidence: {trade.get('confidence')}\n"
        f"  Article title: {trade.get('article_title')}\n"
        f"  Article summary: {trade.get('article_summary')}\n"
        f"  Original reasoning: {trade.get('reasoning')}\n"
        f"  Exited early: {trade.get('left_trade_early')}\n"
        f"  Early exit reason: {trade.get('reason_for_leaving_trade_early')}\n"
        f"  Lesson learned: {trade.get('lesson_learned')}\n"
    )


def generate_synopsis(trades: list[dict], week_start, week_end, base_url: str = "", current_playbook: str = None) -> str:
    if not trades:
        return f"# Weekly Trading Synopsis: {week_start} – {week_end}\n\nNo closed trades were recorded this week."

    trades_text = "\n".join(_format_trade(i + 1, t, base_url) for i, t in enumerate(trades))
    playbook_section = f"Current playbook:\n\n{current_playbook}\n\n" if current_playbook else ""
    user_message = (
        f"Week: {week_start} to {week_end}\n"
        f"Total closed trades: {len(trades)}\n\n"
        f"{playbook_section}"
        f"Trade data:\n\n{trades_text}"
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _build_system_prompt(base_url, current_playbook)},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=16000,
    )

    return response.choices[0].message.content.strip()
