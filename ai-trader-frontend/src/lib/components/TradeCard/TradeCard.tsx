import Link from "next/link";
import styles from "./TradeCard.module.css";
import { Trade, LiveTradeData } from "@/lib/types";

type Props = {
  trade: Trade;
  live?: boolean;
  liveLoading?: boolean;
  liveData?: LiveTradeData | null;
  isNew?: boolean;
};

export default function TradeCard({ trade, live = false, liveLoading = false, liveData = null, isNew = false }: Props) {
  const unrealizedPl = liveData?.unrealizedPl ?? null;

  const pipSize = trade.instrument.includes("JPY") ? 0.01 : 0.0001;
  const isBuy = trade.direction === "buy";

  const canShowBar = liveData?.slPrice != null && liveData?.tpPrice != null && liveData?.entryPrice != null;

  // Derive current price from entry + P/L (P/L ≈ units × price_change for non-cross pairs)
  const currentPrice = canShowBar
    ? (isBuy
        ? liveData!.entryPrice + liveData!.unrealizedPl / trade.units
        : liveData!.entryPrice - liveData!.unrealizedPl / trade.units)
    : null;

  // Pip P/L from actual price movement
  const pips = currentPrice != null
    ? (isBuy ? currentPrice - liveData!.entryPrice : liveData!.entryPrice - currentPrice) / pipSize
    : null;

  // Bar: left=SL (bad), right=TP (good). Position using real price ratios.
  // buy:  slPrice < entry < tpPrice  →  % = (price - sl) / (tp - sl)
  // sell: tpPrice < entry < slPrice  →  % = (sl - price) / (sl - tp)
  const priceToBarPct = (price: number) =>
    isBuy
      ? (price - liveData!.slPrice!) / (liveData!.tpPrice! - liveData!.slPrice!) * 100
      : (liveData!.slPrice! - price) / (liveData!.slPrice! - liveData!.tpPrice!) * 100;

  const entryPct = canShowBar ? priceToBarPct(liveData!.entryPrice) : null;
  const markerPct = canShowBar && currentPrice != null
    ? Math.max(0, Math.min(100, priceToBarPct(currentPrice)))
    : null;

  // Pips remaining until SL and TP
  const pipsToSL = currentPrice != null
    ? (isBuy ? currentPrice - liveData!.slPrice! : liveData!.slPrice! - currentPrice) / pipSize
    : null;
  const pipsToTP = currentPrice != null
    ? (isBuy ? liveData!.tpPrice! - currentPrice : currentPrice - liveData!.tpPrice!) / pipSize
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
        {trade.left_trade_early && (
          <span className={styles.earlyExitBadge}>⎋ Early</span>
        )}
        {trade.trade_status === "closed" && trade.profit_loss != null && (
          <span className={trade.profit_loss >= 0 ? styles.plPositive : styles.plNegative}>
            {trade.profit_loss >= 0 ? "+$" : "-$"}{Math.abs(trade.profit_loss).toFixed(2)}
          </span>
        )}
        {live && (liveLoading
          ? <span className={styles.skeletonPill} />
          : unrealizedPl != null && (
              <span className={unrealizedPl >= 0 ? styles.plPositive : styles.plNegative}>
                {unrealizedPl >= 0 ? "+$" : "-$"}{Math.abs(unrealizedPl).toFixed(2)}
              </span>
            )
        )}
      </div>

      <span className={`${styles.direction} ${trade.direction === "buy" ? styles.buy : styles.sell}`}>
        {trade.direction}
      </span>

      {live && liveLoading && (
        <div className={styles.skeletonProgress}>
          <div className={styles.skeletonProgressHeader}>
            <span className={styles.skeletonChip} style={{ width: 72 }} />
            <span className={styles.skeletonChip} style={{ width: 48 }} />
          </div>
          <div className={styles.skeletonTrack} />
          <div className={styles.skeletonProgressHeader}>
            <span className={styles.skeletonChip} style={{ width: 18 }} />
            <span className={styles.skeletonChip} style={{ width: 18 }} />
          </div>
        </div>
      )}
      {live && !liveLoading && canShowBar && entryPct != null && markerPct != null && pips != null && pipsToSL != null && pipsToTP != null && (
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
            <span>SL {pipsToSL.toFixed(1)}p</span>
            <span>TP {pipsToTP.toFixed(1)}p</span>
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
