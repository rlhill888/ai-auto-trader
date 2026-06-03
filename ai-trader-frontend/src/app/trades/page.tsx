import Link from "next/link";
import { getTrades } from "@/lib/api";
import { Trade } from "@/lib/types";
import styles from "./page.module.css";

export default async function TradesPage() {
  const trades: Trade[] = await getTrades();
  console.log(trades)
  return (
    <main style={{ minHeight: "100vh" }}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>
          ← Back to dashboard
        </Link>

        <div className={styles.header}>
          <h1 className={styles.title}>All Trades</h1>
          <p className={styles.subtitle}>{trades.length} trades recorded</p>
        </div>

        <div className={styles.list}>
          {trades.map((trade) => {
            const date = new Date(trade.timestamp).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            });

            const statusClass =
              trade.trade_status === "open"
                ? styles.statusOpen
                : trade.trade_status === "closed"
                ? styles.statusClosed
                : styles.statusSkipped;

            const outcomeClass =
              trade.trade_status === "skipped" || trade.trade_status === "already_in_trade"
                ? ""
                : trade.is_good_trade
                ? styles.good
                : styles.bad;

            return (
              <Link
                key={trade.trade_id}
                href={`/trades/${trade.trade_id}`}
                className={`${styles.row} ${outcomeClass}`}
              >
                <div className={styles.rowLeft}>
                  <div className={styles.rowTop}>
                    <span className={styles.instrument}>
                      {trade.instrument.replace("_", "/")}
                    </span>
                    {trade.trade_status === "skipped" || trade.trade_status === "already_in_trade" ? (
                      <span className={styles.skipped}>Trade Skipped</span>
                    ) : (
                      <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
                        {trade.direction}
                      </span>
                    )}
                    {trade.trade_status !== "skipped" && trade.trade_status !== "already_in_trade" && (
                      <span className={`${styles.status} ${statusClass}`}>
                        {trade.trade_status}
                      </span>
                    )}
                  </div>
                  <p className={styles.articleTitle}>{trade.article_title}</p>
                </div>

                <div className={styles.rowRight}>
                  <div className={styles.confidence}>
                    <span className={styles.confidenceValue}>
                      {Math.round(trade.confidence * 100)}%
                    </span>
                    <div className={styles.confidenceBar}>
                      <div
                        className={styles.confidenceFill}
                        style={{ width: `${trade.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className={styles.date}>{date}</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </main>
  );
}
