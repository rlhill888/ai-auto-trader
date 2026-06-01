import Link from "next/link";
import styles from "./TradeCard.module.css";
import { Trade } from "@/lib/mockTrades";

type Props = {
  trade: Trade;
  live?: boolean;
};

export default function TradeCard({ trade, live = false }: Props) {
  const formatted = new Date(trade.timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Link href={`/trades/${trade.trade_id}`} className={styles.card}>
      <div className={styles.header}>
        <span className={styles.instrument}>{trade.instrument.replace("_", "/")}</span>
        {live && (
          <span className={styles.liveBadge}>
            <span className={styles.liveDot} />
            Live
          </span>
        )}
      </div>

      <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
        {trade.direction}
      </span>

      <div className={styles.row}>
        <span className={styles.rowLabel}>Units</span>
        <span className={styles.rowValue}>{trade.units.toLocaleString()}</span>
      </div>

      <div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>Confidence</span>
          <span className={styles.rowValue}>{Math.round(trade.confidence * 100)}%</span>
        </div>
        <div className={styles.confidenceBar}>
          <div
            className={styles.confidenceFill}
            style={{ width: `${trade.confidence * 100}%` }}
          />
        </div>
      </div>

      <p className={styles.timestamp}>{formatted}</p>
    </Link>
  );
}
