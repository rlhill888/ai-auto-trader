from asyncio.log import logger

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
1. **Followed?** — Did the trades honor it, violate it, or was it untested this week? Reference specific trades and explain the context in detail.
2. **Did it work?** — When the rule was followed, did it produce better outcomes? Was the rule itself sound given what actually happened this week? Could the rule itself have been the problem — did following it hurt performance? Provide a thorough assessment.
3. **Keep, change, or drop?** — Should this rule stay as-is, be refined, or be removed entirely? If it needs changing, suggest the revised version directly and justify the recommendation with evidence from the week's trades.

Be direct and honest. If a rule was flawed or counterproductive, call it out clearly with specific supporting evidence.""" if current_playbook else ""
    return f"""You are an expert forex trading analyst and coach generating a professional weekly trading synopsis. \
Analyze the trade data provided and produce a rigorous, insightful report formatted in markdown.

**Tone and Voice:** Write in a professional, third-person analytical tone throughout. Do not use first-person language \
("I", "my", "me"). Refer to the trader as "the trader," use passive constructions, or address the reader in second person \
("the trader's position," "the portfolio," "this week's results"). The report should read like a professional analyst's review.

**Depth Requirement:** For every question answered in each section, provide a substantive response of 3 to 5 sentences. \
Do not give one-line answers. Each answer must explain the observation, reference specific trade evidence where available, \
and provide analytical context or actionable implication. Vague or cursory answers are not acceptable.

Structure the report exactly as follows:

1. **Weekly Performance Summary** — Open with a detailed recap of the week: total trades, win rate, net P&L, standout moments, and an overall characterization of the week's trading environment and quality of execution.

2. Then answer each question below, organized under their section headers. Each answer must be 3–5 sentences. Be specific and reference actual trades where relevant. If the data is insufficient to answer a question, provide a brief explanation of what data would be needed and why it matters.

---

### Edge Discovery
- Which trade setups generated the highest expectancy?
- Which article categories produced the largest average moves?
- Which trades had the highest win rate?
- Which trades had the best risk-to-reward ratio?
- Which currencies performed best?
- Which currency pairs warrant increased allocation going forward?
- Which trade types should be eliminated from the strategy?
- Which catalysts consistently created follow-through?
- Which catalysts created fakeouts?

### Timing Analysis
- Did entering immediately after publication outperform waiting for confirmation?
- What entry timing produced the best results?
- How long after publication does market reaction typically peak?
- Which time of day generated the best trades?
- Which trading sessions were most profitable?
- Which day of the week performed best?
- Which day of the week should be avoided or treated with reduced size?

### News Source Analysis
- Which publication generated the most profitable signals?
- Which publication generated the most losing trades?
- Which authors produced the highest-quality signals?
- Which sources consistently report information too late to be actionable?
- Which sources tend to publish market-moving information earliest?
- Which sources create the most noise relative to signal?
- Which sources should be removed from the watchlist?

### Market Environment Analysis
- What market conditions existed during the best-performing trades this week?
- What market conditions existed during the worst-performing trades this week?
- Was volatility a net benefit or net detriment to performance?
- Did trending markets outperform range-bound markets?
- Did high-impact news weeks help or hinder overall performance?
- Were results stronger during risk-on or risk-off market environments?
- Which macro themes dominated the most profitable trades?

### Execution Analysis
- Was the trading plan adhered to consistently throughout the week?
- Which rules were violated most frequently, and what was the cost?
- What execution mistakes repeated across multiple trades?
- How much potential profit was left on the table due to poor entries?
- How much potential profit was forfeited due to premature or poorly-timed exits?
- Were stops being moved too early, and what was the measurable impact?
- Were profits being taken too early before targets were reached?
- Which losing trades were structurally sound and should be viewed as correct process?
- Which winning trades represented poor process despite a favorable outcome?

### Best Performing Themes
Identify the macro or narrative themes (e.g. central bank policy, inflation data, geopolitical risk, risk-on/off sentiment) \
that drove the most profitable trades this week. For each theme: name it, provide a detailed explanation of which trades it \
powered and why the narrative created momentum, assess whether it still has legs going into next week or appears to be \
fading, and offer a recommendation on how to position around it.

---

Use markdown headers, bullet points, bold text, and tables where they add clarity. Be analytical and direct.

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

    logger.info(f"Sending synopsis analysis message to OpenAI: {user_message}")
    response = openai_client.chat.completions.create(
        model="gpt-5.5-2026-04-23",
        messages=[
            {"role": "system", "content": _build_system_prompt(base_url, current_playbook)},
            {"role": "user", "content": user_message},
        ]
    )
    logger.info(f"Received response from OpenAI: {response.choices[0].message.content}")

    return response.choices[0].message.content.strip()
