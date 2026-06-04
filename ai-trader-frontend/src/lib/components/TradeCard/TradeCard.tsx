import Link from "next/link";
import styles from "./TradeCard.module.css";
import { Trade, LiveTradeData } from "@/lib/types";

type Props = {
  trade: Trade;
  live?: boolean;
  liveData?: LiveTradeData | null;
  isNew?: boolean;
};

export default function TradeCard({ trade, live = false, liveData = null, isNew = false }: Props) {
  const unrealizedPl = liveData?.unrealizedPl ?? null;

  const pipSize = trade.instrument.includes("JPY") ? 0.01 : 0.0001;
  const pips = liveData ? liveData.unrealizedPl / (trade.units * pipSize) : null;

  const canShowBar = liveData?.slPrice != null && liveData?.tpPrice != null && liveData?.entryPrice != null && pips != null;
  const SL_PIPS = canShowBar ? Math.abs(liveData!.entryPrice - liveData!.slPrice!) / pipSize : null;
  const TP_PIPS = canShowBar ? Math.abs(liveData!.tpPrice! - liveData!.entryPrice) / pipSize : null;
  const TOTAL_PIPS = SL_PIPS != null && TP_PIPS != null ? SL_PIPS + TP_PIPS : null;
  const entryPct = TOTAL_PIPS != null && SL_PIPS != null ? (SL_PIPS / TOTAL_PIPS) * 100 : null;
  const markerPct = entryPct != null && pips != null && TOTAL_PIPS != null
    ? Math.max(0, Math.min(100, entryPct + (pips / TOTAL_PIPS) * 100))
    : null;
  const formatted = new Date(trade.timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Link href={`/trades/${trade.trade_id}`} className={`${styles.card}${isNew ? ` ${styles.flash}` : ""}`}>
      <div className={styles.header}>
        <span className={`${styles.instrument} ${trade.trade_status === "closed" && trade.is_successful != null ? (trade.is_successful ? styles.instrumentSuccess : styles.instrumentFail) : ""}`}>
          {trade.instrument.replace("_", "/")}
        </span>
        {live && (
          <span className={styles.liveBadge}>
            <span className={styles.liveDot} />
            Live
          </span>
        )}
        {trade.trade_status === "closed" && trade.profit_loss != null && (
          <span className={trade.profit_loss >= 0 ? styles.plPositive : styles.plNegative}>
            {trade.profit_loss >= 0 ? "+$" : "-$"}{Math.abs(trade.profit_loss).toFixed(2)}
          </span>
        )}
        {live && unrealizedPl != null && (
          <span className={unrealizedPl >= 0 ? styles.plPositive : styles.plNegative}>
            {unrealizedPl >= 0 ? "+$" : "-$"}{Math.abs(unrealizedPl).toFixed(2)}
          </span>
        )}
      </div>

      <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
        {trade.direction}
      </span>

      {live && canShowBar && entryPct != null && markerPct != null && (
        <div className={styles.liveProgress}>
          <div className={styles.liveProgressHeader}>
            <span className={styles.rowLabel}>Entry {liveData.entryPrice.toFixed(trade.instrument.includes("JPY") ? 3 : 5)}</span>
            <span className={pips >= 0 ? styles.plPositive : styles.plNegative}>
              {pips >= 0 ? "+" : ""}{pips.toFixed(1)} pips
            </span>
          </div>
          <div
            className={styles.tpSlTrack}
            style={{ '--entry-pct': `${entryPct}%` } as React.CSSProperties}
          >
            <div className={styles.tpSlEntry} style={{ left: `${entryPct}%` }} />
            <div
              className={`${styles.tpSlMarker} ${pips >= 0 ? styles.tpSlMarkerPositive : styles.tpSlMarkerNegative}`}
              style={{ left: `${markerPct}%` }}
            />
          </div>
          <div className={styles.tpSlLabels}>
            <span>SL</span>
            <span>TP</span>
          </div>
        </div>
      )}

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
