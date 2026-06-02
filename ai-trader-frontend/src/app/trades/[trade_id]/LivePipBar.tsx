"use client";

import { useEffect, useState } from "react";
import { LiveTradeData } from "@/lib/types";
import styles from "./LivePipBar.module.css";

type Props = {
  oandaTradeId: string;
  instrument: string;
  units: number;
};

const POLL_INTERVAL_MS = 10_000;

export default function LivePipBar({ oandaTradeId, instrument, units }: Props) {
  const [data, setData] = useState<LiveTradeData | null>(null);

  useEffect(() => {
    async function fetchLive() {
      try {
        const res = await fetch("/api/trades/live");
        if (res.ok) {
          const all = await res.json();
          setData(all[oandaTradeId] ?? null);
        }
      } catch {}
    }

    fetchLive();
    const id = setInterval(fetchLive, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [oandaTradeId]);

  if (!data || data.slPrice == null || data.tpPrice == null) return null;

  const pipSize = instrument.includes("JPY") ? 0.01 : 0.0001;
  const pips = data.unrealizedPl / (units * pipSize);
  const decimals = instrument.includes("JPY") ? 3 : 5;

  const SL_PIPS = Math.abs(data.entryPrice - data.slPrice) / pipSize;
  const TP_PIPS = Math.abs(data.tpPrice - data.entryPrice) / pipSize;
  const TOTAL_PIPS = SL_PIPS + TP_PIPS;
  const entryPct = (SL_PIPS / TOTAL_PIPS) * 100;
  const markerPct = Math.max(0, Math.min(100, entryPct + (pips / TOTAL_PIPS) * 100));

  const isProfit = pips >= 0;

  return (
    <div className={styles.card}>
      <p className={styles.sectionLabel}>Live Position</p>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Unrealized P&L</span>
          <span className={`${styles.statValue} ${isProfit ? styles.positive : styles.negative}`}>
            {isProfit ? "+$" : "-$"}{Math.abs(data.unrealizedPl).toFixed(2)}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Pips</span>
          <span className={`${styles.statValue} ${isProfit ? styles.positive : styles.negative}`}>
            {isProfit ? "+" : ""}{pips.toFixed(1)}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Entry</span>
          <span className={styles.statValue}>{data.entryPrice.toFixed(decimals)}</span>
        </div>
      </div>

      <div className={styles.barWrap}>
        <div
          className={styles.track}
          style={{ "--entry-pct": `${entryPct}%` } as React.CSSProperties}
        >
          <div className={styles.entryTick} style={{ left: `${entryPct}%` }} />
          <div
            className={`${styles.marker} ${isProfit ? styles.markerPositive : styles.markerNegative}`}
            style={{ left: `${markerPct}%` }}
          />
        </div>

        <div className={styles.priceLabels}>
          <span className={styles.slLabel}>SL {data.slPrice.toFixed(decimals)}</span>
          <span className={styles.tpLabel}>TP {data.tpPrice.toFixed(decimals)}</span>
        </div>
      </div>
    </div>
  );
}
