import Link from "next/link";
import { notFound } from "next/navigation";
import parse from "html-react-parser";
import { getTrade } from "@/lib/api";
import styles from "./page.module.css";
import LivePipBar from "./LivePipBar";

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
        <div className={styles.topBar}>
          <Link href="/" className={styles.back}>
            ← Back to dashboard
          </Link>
          {trade.article_id && (
            <a href={trade.article_id} target="_blank" rel="noopener noreferrer" className={styles.articleLink}>
              Article Link ↗
            </a>
          )}
        </div>

        <div className={styles.header}>
          <p className={styles.instrument}>{trade.instrument.replace("_", "/")}</p>
          <h1 className={styles.title}>{trade.article_title}</h1>
          <div className={styles.meta}>
            {trade.trade_status === "skipped" || trade.trade_status === "already_in_trade" ? (
              <span className={styles.skipped}>Trade Skipped</span>
            ) : (
              <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
                {trade.direction}
              </span>
            )}
            {trade.trade_status === "open" && (
              <span className={styles.liveBadge}>
                <span className={styles.liveDot} />
                Live
              </span>
            )}
            <span className={styles.metaText}>{trade.units.toLocaleString()} units</span>
            <span className={styles.metaText}>·</span>
            <span className={styles.metaText}>{formatted}</span>
          </div>
        </div>

        {trade.trade_status === "open" && (
          <LivePipBar
            oandaTradeId={trade.oanda_trade_id}
            instrument={trade.instrument}
            units={trade.units}
          />
        )}

        <div className={styles.card}>
          <p className={styles.sectionLabel}>Article Summary</p>
          <div className={styles.body}>{parse(trade.article_summary)}</div>
        </div>

        <div className={styles.card}>
          <p className={styles.sectionLabel}>AI Reasoning</p>
          {
            trade.trade_status === "already_in_trade" ?

              <p className={styles.body}>This trade was skipped because an existing position in this instrument was already open at the time of analysis.</p>
              :
              <p className={styles.body}>{trade.reasoning}</p>
          }

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

        {trade.trade_status !== "open" && trade.lesson_learned && (
          <div className={`${styles.lesson} ${trade.is_successful == null ? styles.lessonNeutral : trade.is_successful ? styles.lessonGood : styles.lessonBad}`}>
            <p className={styles.sectionLabel}>Lesson Learned</p>
            <p className={styles.lessonBody}>{trade.lesson_learned}</p>
          </div>
        )}
      </div>
    </main>
  );
}
