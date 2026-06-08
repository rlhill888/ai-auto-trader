import json
import logging
import re
from datetime import timedelta

from config import FRONTEND_BASE_URL
from dynamodb import get_current_playbook, store_current_playbook
from storage import get_closed_trades_for_week, store_weekly_report
from synopsis import generate_synopsis
from utils import resolve_week_start
from weekly_lesson import generate_weekly_lesson

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Weekly synopsis lambda invoked")

    try:
        week_start = resolve_week_start(event)
        week_end = week_start + timedelta(days=7)
        logger.info("Querying trades for week %s to %s", week_start, week_end)

        trades = get_closed_trades_for_week(week_start, week_end)
        logger.info("Found %d closed trade(s) for the week", len(trades))

        current_playbook = get_current_playbook()
        if current_playbook:
            logger.info("Existing playbook found, including in analysis")

        synopsis = generate_synopsis(trades, week_start, week_end, base_url=FRONTEND_BASE_URL, current_playbook=current_playbook)
        logger.info("Synopsis generated (%d chars)", len(synopsis))

        weekly_lesson = generate_weekly_lesson(trades, week_start, week_end, synopsis=synopsis, current_playbook=current_playbook)
        logger.info("Weekly lesson generated (%d chars)", len(weekly_lesson))

        playbook = weekly_lesson.get("next_week_playbook")
        if playbook:
            marker = "## Next Week's Playbook"
            rules_section = playbook[playbook.index(marker):] if marker in playbook else playbook
            rule_lines = re.findall(r"^\d+\.\s+\*\*DO\b.*\*\*", rules_section, re.MULTILINE)
            rules_only = "\n".join(rule_lines) if rule_lines else rules_section
            store_current_playbook(rules_only)
            logger.info("Playbook stored in DynamoDB (%d rules)", len(rule_lines))

        store_weekly_report(
            week_start=week_start,
            week_end=week_end,
            trade_count=len(trades),
            synopsis=synopsis,
            weekly_lesson=weekly_lesson.get("weekly_lesson_learned"),
            key_insights=weekly_lesson.get("key_insights"),
            biggest_mistakes=weekly_lesson.get("biggest_mistakes"),
            best_performing_themes=weekly_lesson.get("best_performing_themes"),
            new_playbook_rules=weekly_lesson.get("next_week_playbook"),
        )
        logger.info("Weekly report stored in database")

        return {
            "statusCode": 200,
            "body": json.dumps({"synopsis": synopsis, "weekly_lesson": weekly_lesson}),
        }
    except Exception:
        logger.exception("Error generating weekly synopsis")
        raise
