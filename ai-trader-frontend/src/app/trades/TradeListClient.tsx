"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { Trade } from "@/lib/types";
import styles from "./page.module.css";

const PAGE_SIZE = 40;

export default function TradeListClient({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState<Trade[]>(initialTrades);
  const [hasMore, setHasMore] = useState(initialTrades.length === PAGE_SIZE);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const offsetRef = useRef(initialTrades.length);
  const isLoadingRef = useRef(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(async () => {
    if (isLoadingRef.current) return;
    isLoadingRef.current = true;
    setIsLoadingMore(true);
    const res = await fetch(`/api/trades?limit=${PAGE_SIZE}&offset=${offsetRef.current}`);
    if (res.ok) {
      const next: Trade[] = await res.json();
      if (next.length < PAGE_SIZE) setHasMore(false);
      if (next.length > 0) {
        offsetRef.current += next.length;
        setTrades((prev) => {
          const existingIds = new Set(prev.map((t) => t.trade_id));
          return [...prev, ...next.filter((t) => !existingIds.has(t.trade_id))];
        });
      }
    }
    isLoadingRef.current = false;
    setIsLoadingMore(false);
  }, []);

  useEffect(() => {
    if (!hasMore) return;
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) loadMore();
      },
      { rootMargin: "200px" }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadMore]);

  return (
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

      {hasMore && (
        <div ref={sentinelRef} style={{ height: 1 }}>
          {isLoadingMore && (
            <p style={{ textAlign: "center", color: "#999", padding: "16px 0", fontSize: 13 }}>
              Loading more trades…
            </p>
          )}
        </div>
      )}
    </div>
  );
}
