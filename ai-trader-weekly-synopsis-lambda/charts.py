import io
import logging
import os
import re
from datetime import date, datetime
from urllib.parse import quote

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

import boto3
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

S3_BUCKET = "auto-ai-trader-charts"

s3 = boto3.client("s3")

WIN_COLOR = "#2ca02c"
LOSS_COLOR = "#d62728"
NEUTRAL_COLOR = "#1f77b4"

DURATION_RE = re.compile(r"(\d+)\s*(minute|hour|day)", re.IGNORECASE)

CHART_TITLES = {
    "01_cumulative_pl": "Cumulative P/L",
    "02_pl_per_trade": "P/L Per Trade",
    "03_win_rate_by_instrument": "Win Rate by Instrument",
    "04_avg_pl_by_instrument": "Avg P/L by Instrument",
    "05_avg_pl_by_direction": "Avg P/L by Direction",
    "06_confidence_vs_pl": "Confidence vs P/L",
    "07_win_rate_by_confidence_bucket": "Win Rate by Confidence Bucket",
    "08_good_trade_vs_outcome": "Prediction vs Outcome",
    "09_trade_count_by_hour": "Trade Count by Hour",
    "10_avg_pl_by_hour": "Avg P/L by Hour",
    "11_exit_timing_status": "Exit Timing",
    "12_estimated_vs_actual_duration": "Estimated vs Actual Duration",
    "13_trade_status_breakdown": "Trade Status Breakdown",
    "14_early_exit_impact": "Early Exit Impact",
    "15_units_vs_pl": "Units vs P/L",
}

CHART_DESCRIPTIONS = {
    "01_cumulative_pl": "Cumulative P/L over time — shows the overall profit/loss trajectory across all closed trades for the week.",
    "02_pl_per_trade": "P/L per trade — each bar is one trade (green = win, red = loss), ordered chronologically.",
    "03_win_rate_by_instrument": "Win rate by instrument — percentage of winning trades for each traded symbol.",
    "04_avg_pl_by_instrument": "Average P/L by instrument — mean profit or loss per trade for each symbol.",
    "05_avg_pl_by_direction": "Average P/L by direction — compares mean P/L for long vs short trades.",
    "06_confidence_vs_pl": "Confidence vs P/L — scatter plot showing whether higher AI confidence correlates with better outcomes.",
    "07_win_rate_by_confidence_bucket": "Win rate by confidence bucket — win percentage grouped into 20-point confidence bands (0–100).",
    "08_good_trade_vs_outcome": "Trade prediction vs outcome — 4-category breakdown of good/bad prediction vs win/loss result.",
    "09_trade_count_by_hour": "Trade count by hour — how many trades were opened each hour of the day (UTC).",
    "10_avg_pl_by_hour": "Average P/L by hour — mean profit/loss by hour of day, showing which times performed best.",
    "11_exit_timing_status": "Exit timing — how many trades were exited early, on time, or late relative to the estimated end.",
    "12_estimated_vs_actual_duration": "Estimated vs actual duration — compares the AI's predicted trade length to how long trades actually ran.",
    "13_trade_status_breakdown": "Trade status breakdown — pie chart of all trade statuses (closed, open, cancelled, etc.).",
    "14_early_exit_impact": "Early exit impact — average P/L for trades exited early vs trades held the full course.",
    "15_units_vs_pl": "Units vs P/L — scatter plot showing whether position size (units) relates to profit or loss.",
}


def generate_weekly_charts(
    trades_closed: list[dict],
    trades_all: list[dict],
    week_start: date,
    week_end: date,
) -> list[str]:
    df_closed = _prepare_closed_df(trades_closed)
    df_all = _prepare_all_df(trades_all)

    folder = f"{week_start.isoformat()}_to_{week_end.isoformat()}"
    builders = [
        ("01_cumulative_pl", lambda: _chart_cumulative_pl(df_closed)),
        ("02_pl_per_trade", lambda: _chart_pl_per_trade(df_closed)),
        ("03_win_rate_by_instrument", lambda: _chart_win_rate_by_instrument(df_closed)),
        ("04_avg_pl_by_instrument", lambda: _chart_avg_pl_by_instrument(df_closed)),
        ("05_avg_pl_by_direction", lambda: _chart_avg_pl_by_direction(df_closed)),
        ("06_confidence_vs_pl", lambda: _chart_confidence_vs_pl(df_closed)),
        ("07_win_rate_by_confidence_bucket", lambda: _chart_win_rate_by_confidence_bucket(df_closed)),
        ("08_good_trade_vs_outcome", lambda: _chart_good_trade_vs_outcome(df_closed)),
        ("09_trade_count_by_hour", lambda: _chart_trade_count_by_hour(df_all)),
        ("10_avg_pl_by_hour", lambda: _chart_avg_pl_by_hour(df_closed)),
        ("11_exit_timing_status", lambda: _chart_exit_timing_status(df_closed)),
        ("12_estimated_vs_actual_duration", lambda: _chart_estimated_vs_actual_duration(df_closed)),
        ("13_trade_status_breakdown", lambda: _chart_trade_status_breakdown(df_all)),
        ("14_early_exit_impact", lambda: _chart_early_exit_impact(df_closed)),
        ("15_units_vs_pl", lambda: _chart_units_vs_pl(df_closed)),
    ]

    uploaded_keys = []
    for filename, builder in builders:
        try:
            fig = builder()
            if fig is None:
                logger.warning("Skipping chart %s: no data available", filename)
                continue
            key = f"{folder}/{filename}.png"
            _save_and_upload(fig, key)
            uploaded_keys.append(key)
        except Exception:
            logger.exception("Failed to build/upload chart %s", filename)

    logger.info("Uploaded %d chart(s) to s3://%s/%s/", len(uploaded_keys), S3_BUCKET, folder)
    return uploaded_keys


def _prepare_closed_df(trades: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(trades)
    if df.empty:
        return df
    for col in ("timestamp", "closed_at", "estimated_latest_trade_end"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    if "profit_loss" in df.columns:
        df["profit_loss"] = pd.to_numeric(df["profit_loss"], errors="coerce")
    if "confidence" in df.columns:
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    if "units" in df.columns:
        df["units"] = pd.to_numeric(df["units"], errors="coerce")
    return df


def _prepare_all_df(trades: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(trades)
    if df.empty:
        return df
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    if "profit_loss" in df.columns:
        df["profit_loss"] = pd.to_numeric(df["profit_loss"], errors="coerce")
    return df


def _save_and_upload(fig, key: str) -> None:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    chart_name = key.split("/")[-1].removesuffix(".png")
    metadata: dict[str, str] = {}
    if title := CHART_TITLES.get(chart_name):
        metadata["title"] = quote(title)
    if description := CHART_DESCRIPTIONS.get(chart_name):
        metadata["description"] = quote(description)
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buf.getvalue(), ContentType="image/png", Metadata=metadata)


def _new_fig():
    fig, ax = plt.subplots(figsize=(10, 6))
    return fig, ax


def _confidence_scale(series: pd.Series) -> pd.Series:
    series = series.dropna()
    if series.empty:
        return series
    if series.max() <= 1:
        return series * 100
    return series


# --- Performance ---

def _chart_cumulative_pl(df: pd.DataFrame):
    if df.empty or "closed_at" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["closed_at", "profit_loss"]).sort_values("closed_at")
    if data.empty:
        return None
    cumulative = data["profit_loss"].cumsum()
    fig, ax = _new_fig()
    ax.plot(data["closed_at"], cumulative, marker="o", color=NEUTRAL_COLOR)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title("Cumulative P/L Over Time")
    ax.set_xlabel("Closed At")
    ax.set_ylabel("Cumulative P/L")
    fig.autofmt_xdate()
    return fig


def _chart_pl_per_trade(df: pd.DataFrame):
    if df.empty or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["profit_loss"]).sort_values("closed_at") if "closed_at" in df.columns else df.dropna(subset=["profit_loss"])
    if data.empty:
        return None
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in data["profit_loss"]]
    fig, ax = _new_fig()
    ax.bar(range(len(data)), data["profit_loss"], color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("P/L Per Trade")
    ax.set_xlabel("Trade (chronological)")
    ax.set_ylabel("Profit / Loss")
    return fig


def _chart_win_rate_by_instrument(df: pd.DataFrame):
    if df.empty or "instrument" not in df.columns or "is_successful" not in df.columns:
        return None
    data = df.dropna(subset=["instrument"])
    if data.empty:
        return None
    win_rate = data.groupby("instrument")["is_successful"].apply(lambda s: s.fillna(False).mean() * 100)
    if win_rate.empty:
        return None
    fig, ax = _new_fig()
    win_rate.sort_values(ascending=False).plot(kind="bar", ax=ax, color=NEUTRAL_COLOR)
    ax.set_title("Win Rate by Instrument")
    ax.set_xlabel("Instrument")
    ax.set_ylabel("Win Rate (%)")
    ax.set_ylim(0, 100)
    return fig


def _chart_avg_pl_by_instrument(df: pd.DataFrame):
    if df.empty or "instrument" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["instrument", "profit_loss"])
    if data.empty:
        return None
    avg_pl = data.groupby("instrument")["profit_loss"].mean().sort_values(ascending=False)
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in avg_pl]
    avg_pl.plot(kind="bar", ax=ax, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Average P/L by Instrument")
    ax.set_xlabel("Instrument")
    ax.set_ylabel("Average P/L")
    return fig


def _chart_avg_pl_by_direction(df: pd.DataFrame):
    if df.empty or "direction" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["direction", "profit_loss"])
    if data.empty:
        return None
    avg_pl = data.groupby("direction")["profit_loss"].mean()
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in avg_pl]
    avg_pl.plot(kind="bar", ax=ax, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Average P/L by Direction")
    ax.set_xlabel("Direction")
    ax.set_ylabel("Average P/L")
    return fig


# --- AI quality ---

def _chart_confidence_vs_pl(df: pd.DataFrame):
    if df.empty or "confidence" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["confidence", "profit_loss"]).copy()
    if data.empty:
        return None
    data["confidence"] = _confidence_scale(data["confidence"])
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in data["profit_loss"]]
    ax.scatter(data["confidence"], data["profit_loss"], c=colors, alpha=0.7)
    if len(data) >= 2 and data["confidence"].nunique() > 1:
        coeffs = np.polyfit(data["confidence"], data["profit_loss"], 1)
        trend_x = np.linspace(data["confidence"].min(), data["confidence"].max(), 50)
        trend_y = np.polyval(coeffs, trend_x)
        ax.plot(trend_x, trend_y, color="black", linestyle="--", linewidth=1.5, label="Trend")
        ax.legend()
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Confidence vs Profit/Loss")
    ax.set_xlabel("Confidence (%)")
    ax.set_ylabel("Profit / Loss")
    return fig


def _chart_win_rate_by_confidence_bucket(df: pd.DataFrame):
    if df.empty or "confidence" not in df.columns or "is_successful" not in df.columns:
        return None
    data = df.dropna(subset=["confidence"]).copy()
    if data.empty:
        return None
    data["confidence"] = _confidence_scale(data["confidence"])
    bins = [0, 20, 40, 60, 80, 100]
    labels = ["0-20", "21-40", "41-60", "61-80", "81-100"]
    data["bucket"] = pd.cut(data["confidence"], bins=bins, labels=labels, include_lowest=True)
    win_rate = data.groupby("bucket", observed=True)["is_successful"].apply(lambda s: s.fillna(False).mean() * 100)
    if win_rate.empty:
        return None
    fig, ax = _new_fig()
    win_rate.reindex(labels).plot(kind="bar", ax=ax, color=NEUTRAL_COLOR)
    ax.set_title("Win Rate by Confidence Bucket")
    ax.set_xlabel("Confidence Bucket (%)")
    ax.set_ylabel("Win Rate (%)")
    ax.set_ylim(0, 100)
    return fig


def _chart_good_trade_vs_outcome(df: pd.DataFrame):
    if df.empty or "is_good_trade" not in df.columns or "is_successful" not in df.columns:
        return None
    data = df.dropna(subset=["is_good_trade", "is_successful"])
    if data.empty:
        return None
    categories = {
        "Good + Won": ((data["is_good_trade"] == True) & (data["is_successful"] == True)).sum(),
        "Good + Lost": ((data["is_good_trade"] == True) & (data["is_successful"] == False)).sum(),
        "Bad + Won": ((data["is_good_trade"] == False) & (data["is_successful"] == True)).sum(),
        "Bad + Lost": ((data["is_good_trade"] == False) & (data["is_successful"] == False)).sum(),
    }
    fig, ax = _new_fig()
    ax.bar(categories.keys(), categories.values(), color=[WIN_COLOR, LOSS_COLOR, LOSS_COLOR, WIN_COLOR])
    ax.set_title("is_good_trade Prediction vs Actual Outcome")
    ax.set_ylabel("Trade Count")
    return fig


# --- Timing ---

def _chart_trade_count_by_hour(df: pd.DataFrame):
    if df.empty or "timestamp" not in df.columns:
        return None
    data = df.dropna(subset=["timestamp"])
    if data.empty:
        return None
    counts = data["timestamp"].dt.hour.value_counts().reindex(range(24), fill_value=0).sort_index()
    fig, ax = _new_fig()
    counts.plot(kind="bar", ax=ax, color=NEUTRAL_COLOR)
    ax.set_title("Trade Count by Hour of Day (UTC)")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Trade Count")
    return fig


def _chart_avg_pl_by_hour(df: pd.DataFrame):
    if df.empty or "timestamp" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["timestamp", "profit_loss"])
    if data.empty:
        return None
    avg_pl = data.groupby(data["timestamp"].dt.hour)["profit_loss"].mean().reindex(range(24))
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in avg_pl.fillna(0)]
    avg_pl.plot(kind="bar", ax=ax, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Average P/L by Hour of Day (UTC)")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Average P/L")
    return fig


def _chart_exit_timing_status(df: pd.DataFrame, tolerance_minutes: int = 15):
    if df.empty or "estimated_latest_trade_end" not in df.columns or "closed_at" not in df.columns:
        return None
    data = df.dropna(subset=["estimated_latest_trade_end", "closed_at"]).copy()
    if data.empty:
        return None
    diff_minutes = (data["closed_at"] - data["estimated_latest_trade_end"]).dt.total_seconds() / 60

    def classify(d):
        if d < -tolerance_minutes:
            return "Early"
        if d > tolerance_minutes:
            return "Late"
        return "On Time"

    status = diff_minutes.apply(classify)
    counts = status.value_counts().reindex(["Early", "On Time", "Late"], fill_value=0)
    fig, ax = _new_fig()
    counts.plot(kind="bar", ax=ax, color=[NEUTRAL_COLOR, WIN_COLOR, LOSS_COLOR])
    ax.set_title(f"Exit Timing Status (±{tolerance_minutes}min tolerance)")
    ax.set_xlabel("Status")
    ax.set_ylabel("Trade Count")
    return fig


def _parse_duration_to_minutes(text) -> float | None:
    if not isinstance(text, str):
        return None
    match = DURATION_RE.search(text)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2).lower()
    multiplier = {"minute": 1, "hour": 60, "day": 1440}[unit]
    return value * multiplier


def _chart_estimated_vs_actual_duration(df: pd.DataFrame):
    if df.empty or "estimated_trade_timeframe" not in df.columns or "timestamp" not in df.columns or "closed_at" not in df.columns:
        return None
    data = df.dropna(subset=["timestamp", "closed_at"]).copy()
    if data.empty:
        return None
    data["estimated_minutes"] = data["estimated_trade_timeframe"].apply(_parse_duration_to_minutes)
    parsed = data.dropna(subset=["estimated_minutes"])
    skipped = len(data) - len(parsed)
    if skipped:
        logger.info("Excluded %d trade(s) with unparseable estimated_trade_timeframe", skipped)
    if parsed.empty:
        return None
    parsed = parsed.copy()
    parsed["actual_minutes"] = (parsed["closed_at"] - parsed["timestamp"]).dt.total_seconds() / 60
    parsed["estimated_bucket"] = parsed["estimated_trade_timeframe"]
    comparison = parsed.groupby("estimated_bucket")[["estimated_minutes", "actual_minutes"]].mean()
    if comparison.empty:
        return None
    fig, ax = _new_fig()
    comparison.plot(kind="bar", ax=ax, color=[NEUTRAL_COLOR, "#ff7f0e"])
    ax.set_title("Estimated vs Actual Trade Duration")
    ax.set_xlabel("Estimated Timeframe (as labeled by AI)")
    ax.set_ylabel("Minutes")
    return fig


# --- Behavior / operations ---

def _chart_trade_status_breakdown(df: pd.DataFrame):
    if df.empty or "trade_status" not in df.columns:
        return None
    counts = df["trade_status"].fillna("unknown").value_counts()
    if counts.empty:
        return None
    fig, ax = _new_fig()
    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.0f%%",
        wedgeprops={"width": 0.4},
        startangle=90,
    )
    ax.set_title("Trade Status Breakdown")
    return fig


def _chart_early_exit_impact(df: pd.DataFrame):
    if df.empty or "left_trade_early" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["left_trade_early", "profit_loss"])
    if data.empty:
        return None
    avg_pl = data.groupby("left_trade_early")["profit_loss"].mean()
    avg_pl.index = ["Left Early" if v else "Held Full Course" for v in avg_pl.index]
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in avg_pl]
    avg_pl.plot(kind="bar", ax=ax, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Early Exit Impact on P/L")
    ax.set_ylabel("Average P/L")
    return fig


def _chart_units_vs_pl(df: pd.DataFrame):
    if df.empty or "units" not in df.columns or "profit_loss" not in df.columns:
        return None
    data = df.dropna(subset=["units", "profit_loss"])
    if data.empty:
        return None
    fig, ax = _new_fig()
    colors = [WIN_COLOR if v >= 0 else LOSS_COLOR for v in data["profit_loss"]]
    ax.scatter(data["units"], data["profit_loss"], c=colors, alpha=0.7)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Units vs Profit/Loss")
    ax.set_xlabel("Units")
    ax.set_ylabel("Profit / Loss")
    return fig
