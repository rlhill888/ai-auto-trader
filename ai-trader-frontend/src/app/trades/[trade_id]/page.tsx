import Link from "next/link";
import { notFound } from "next/navigation";
import { mockTrades } from "@/lib/mockTrades";
import styles from "./page.module.css";

function getLesson(trade: (typeof mockTrades)[0]): string {
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
  const trade = mockTrades.find((t) => t.trade_id === trade_id);

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
    <main style={{ minHeight: "100vh" }}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>
          ← Back to dashboard
        </Link>

        <div className={styles.header}>
          <p className={styles.instrument}>{trade.instrument.replace("_", "/")}</p>
          <h1 className={styles.title}>{trade.article_title}</h1>
          <div className={styles.meta}>
            <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
              {trade.direction}
            </span>
            <span className={styles.metaText}>{trade.units.toLocaleString()} units</span>
            <span className={styles.metaText}>·</span>
            <span className={styles.metaText}>{formatted}</span>
          </div>
        </div>

        <hr className={styles.divider} />

        <p className={styles.sectionLabel}>Article Summary</p>
        <p className={styles.body}>{trade.article_summary}</p>

        <hr className={styles.divider} />

        <p className={styles.sectionLabel}>AI Reasoning</p>
        <p className={styles.body}>{trade.reasoning}</p>

        <hr className={styles.divider} />

        <p className={styles.sectionLabel}>Confidence</p>
        <div className={styles.confidenceRow}>
          <span className={styles.confidenceValue}>{Math.round(trade.confidence * 100)}%</span>
          <div className={styles.confidenceBar}>
            <div className={styles.confidenceFill} style={{ width: `${trade.confidence * 100}%` }} />
          </div>
        </div>

        <hr className={styles.divider} />

        <p className={styles.sectionLabel}>Lesson Learned</p>
        <div className={styles.lesson}>
          <p className={styles.lessonBody}>{getLesson(trade)}</p>
        </div>
      </div>
    </main>
  );
}
