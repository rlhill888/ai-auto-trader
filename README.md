# ai-auto-trader

**Deployed App:** https://main.d2jf8zrd3yfra.amplifyapp.com/

An autonomous forex trading system that reads financial news, decides whether a headline represents a tradeable opportunity, and executes, monitors, and exits trades on OANDA without manual intervention.

The system watches a financial news feed in real time, has a language model judge each article for trading signal, sizes and places the trade automatically, then keeps watching the position — closing it early if a contradicting signal shows up, periodically re-evaluating it against the live market, and writing a "lesson learned" once it closes. Every week it reviews its own closed trades and updates its own playbook of rules for future decisions.

## How it works

```
RSS feed → polling-article-lambda → SQS queue → analysis-trading-lambda → OANDA
                                                          │
                                                          ▼
                                                     DynamoDB (trades, articles, daily stats)
                                                          │
                          ai-trade-checker (scheduled) ───┤
                          ai-trader-weekly-synopsis ──────┘
                                                          │
                                                          ▼
                                                  ai-trader-frontend (Next.js dashboard)
```

1. **polling-article-lambda** polls a financial news RSS feed on a schedule (only while the forex market is open), de-dupes articles against DynamoDB, and pushes new ones onto an SQS FIFO queue.
2. **analysis-trading-lambda** consumes the queue, sends each article to an LLM for a structured trade decision (instrument, direction, confidence, stop loss/take profit in pips, recheck cadence), and if the model is confident enough, sizes the position against account risk (0.5% per trade) and places the order on OANDA. If a new signal contradicts an already-open position, it runs an early-exit evaluation and can flip the trade.
3. **ai-trade-checker** runs on a schedule to reconcile open trades against OANDA's live state — marking trades closed/cancelled, detecting manual closes, generating a written lesson-learned for every closed trade, and triggering an AI "recheck" on still-open trades once their model-assigned recheck interval elapses (closing early if the AI thinks the thesis no longer holds).
4. **reset-daily-ai-trading-values-lambda** runs nightly to snapshot the day's P&L/win-loss stats and reset the daily counters.
5. **ai-trader-weekly-synopsis-lambda** runs weekly, summarizes the week's closed trades with an LLM, extracts lessons and best/worst-performing themes, and writes a new rules "playbook" that gets fed back into every future trading decision. It also generates up to 15 performance charts (using matplotlib) and uploads them to S3
6. **ai-trader-frontend** is a Next.js dashboard showing account stats, open/closed trades, weekly synopses, and a live feed of trade and stats events pushed over Ably.

## Components

| Directory | Purpose |
|---|---|
| `polling-article-lambda/` | Polls RSS feed, dedupes articles, enqueues to SQS |
| `analysis-trading-lambda/` | LLM trade analysis, sizing, order execution, early-exit logic |
| `ai-trade-checker/` | Reconciles trade state with OANDA, lesson generation, periodic AI rechecks |
| `reset-daily-ai-trading-values-lambda/` | Nightly daily-stats rollover |
| `ai-trader-weekly-synopsis-lambda/` | Weekly performance synopsis and playbook generation |
| `ai-trader-frontend/` | Next.js dashboard (trades, account summary, live updates, chart carousel on weekly synopsis pages) |

## Stack

- **Compute:** AWS Lambda (Python 3.14), triggered by EventBridge schedules and SQS
- **Data:** DynamoDB (articles, trades, daily/global stats), Postgres via `pg8000` for richer querying
- **Broker:** OANDA REST API (practice or live environment)
- **AI:** OpenAI for trade analysis, early-exit/recheck decisions, and lesson/synopsis generation
- **Realtime:** Ably for pushing trade/stat events to the frontend
- **Frontend:** Next.js 16, React 19, Recharts, Supabase client
- **CI/CD:** GitHub Actions deploys each Lambda directory independently on push to `main`

## Configuration

Each Lambda reads its secrets (`OPENAI_API_KEY`, `OANDA_API_KEY`, `OANDA_ACCOUNT_ID`, `DATABASE_URL`, `ABLY_API_KEY`) from AWS Secrets Manager via a `SECRET_NAME` environment variable, plus a few plain environment variables (table names, queue URLs, `OANDA_ENVIRONMENT`). The frontend reads its own `.env` for Supabase, DynamoDB, and Ably credentials.

Risk parameters (per-trade risk %, default stop/take-profit) live in each lambda's `config.py` and can be tuned without touching trading logic.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy-lambdas.yml`, which builds and zips each Lambda directory and updates the corresponding function via `aws lambda update-function-code`. The frontend deploys separately via Amplify.
