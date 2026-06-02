import Link from "next/link";
import { notFound } from "next/navigation";
import parse from "html-react-parser";
import { getTrade } from "@/lib/api";
import { Trade } from "@/lib/types";
import styles from "./page.module.css";

function getLesson(trade: Trade): string {
  if (trade.trade_status === "skipped") {
    return `This trade was skipped due to low confidence (${Math.round(trade.confidence * 100)}%). The AI determined there was insufficient directional clarity to commit capital. Monitoring news signals without executing is a valid risk management strategy.`;
  }
  if (trade.is_good_trade) {
    return `The news signal aligned well with a clear macroeconomic narrative, producing a high-confidence directional call. Trades like this — driven by central bank policy or hard economic data — tend to have more predictable short-term outcomes.`;
  }
  return `Despite execution, the underlying signal was ambiguous. Future improvements could include raising the minimum confidence threshold or requiring corroborating signals before entering positions on similar setups.`;
}

export default async function TradePage({
  params,
}: {
  params: Promise<{ trade_id: string }>;
}) {
  const { trade_id } = await params;
  const trade = await getTrade(trade_id);

  if (!trade) notFound();

  const formatted = new Date(trade.timestamp).toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <main style={{ minHeight: "100vh", background: "#ffffff" }}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>
          ← Back to dashboard
        </Link>

        <div className={styles.header}>
          <p className={styles.instrument}>{trade.instrument.replace("_", "/")}</p>
          <h1 className={styles.title}>{trade.article_title}</h1>
          <div className={styles.meta}>
            {trade.trade_status === "skipped" ? (
              <span className={styles.skipped}>Trade Skipped</span>
            ) : (
              <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
                {trade.direction}
              </span>
            )}
            <span className={styles.metaText}>{trade.units.toLocaleString()} units</span>
            <span className={styles.metaText}>·</span>
            <span className={styles.metaText}>{formatted}</span>
          </div>
        </div>

        <div className={styles.card}>
          <p className={styles.sectionLabel}>Article Summary</p>
          <div className={styles.body}>{parse(trade.article_summary)}</div>
        </div>

        <div className={styles.card}>
          <p className={styles.sectionLabel}>AI Reasoning</p>
          <p className={styles.body}>{trade.reasoning}</p>
        </div>

        <div className={styles.card}>
          <p className={styles.sectionLabel}>Confidence</p>
          <div className={styles.confidenceRow}>
            <span className={styles.confidenceValue}>{Math.round(trade.confidence * 100)}%</span>
            <div className={styles.confidenceBar}>
              <div className={styles.confidenceFill} style={{ width: `${trade.confidence * 100}%` }} />
            </div>
          </div>
        </div>

        <div className={`${styles.lesson} ${trade.trade_status === "skipped" ? styles.lessonNeutral : trade.is_good_trade ? styles.lessonGood : styles.lessonBad}`}>
          <p className={styles.sectionLabel}>Lesson Learned</p>
          <p className={styles.lessonBody}>{getLesson(trade)}</p>
        </div>
      </div>
    </main>
  );
}
