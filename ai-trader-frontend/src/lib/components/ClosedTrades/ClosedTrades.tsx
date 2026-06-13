"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import styles from "./ClosedTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { Trade } from "@/lib/types";

const PAGE_SIZE = 20;

export default function ClosedTrades({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState<Trade[]>(initialTrades);
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());
  const [hasMore, setHasMore] = useState(initialTrades.length === PAGE_SIZE);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const offsetRef = useRef(initialTrades.length);
  const isLoadingRef = useRef(false);
  const rowRef = useRef<HTMLDivElement>(null);
  const knownIdsRef = useRef<Set<string>>(new Set(initialTrades.map((t) => t.trade_id)));

  const loadMore = useCallback(async () => {
    if (isLoadingRef.current || !hasMore) return;
    isLoadingRef.current = true;
    setIsLoadingMore(true);
    const res = await fetch(
      `/api/trades?status=closed&limit=${PAGE_SIZE}&offset=${offsetRef.current}`
    );
    if (res.ok) {
      const next: Trade[] = await res.json();
      if (next.length < PAGE_SIZE) setHasMore(false);
      if (next.length > 0) {
        offsetRef.current += next.length;
        setTrades((prev) => {
          const existingIds = new Set(prev.map((t) => t.trade_id));
          const deduped = next.filter((t) => !existingIds.has(t.trade_id));
          deduped.forEach((t) => knownIdsRef.current.add(t.trade_id));
          return [...prev, ...deduped];
        });
      }
    }
    isLoadingRef.current = false;
    setIsLoadingMore(false);
  }, [hasMore]);

  useEffect(() => {
    const el = rowRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.scrollLeft + el.clientWidth >= el.scrollWidth - 150) loadMore();
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [loadMore]);

  const refetch = useCallback(async () => {
    const res = await fetch(`/api/trades?status=closed&limit=${PAGE_SIZE}&offset=0`);
    if (!res.ok) return;
    const next: Trade[] = await res.json();
    const newTrades = next.filter((t) => !knownIdsRef.current.has(t.trade_id));
    if (newTrades.length > 0) {
      setFlashIds(new Set(newTrades.map((t) => t.trade_id)));
      setTimeout(() => setFlashIds(new Set()), 1100);
      setTrades((prev) => {
        const existingIds = new Set(prev.map((t) => t.trade_id));
        const toAdd = newTrades.filter((t) => !existingIds.has(t.trade_id));
        toAdd.forEach((t) => knownIdsRef.current.add(t.trade_id));
        offsetRef.current += toAdd.length;
        return [...toAdd, ...prev];
      });
    }
  }, []);

  useAblyChannel("trading", "trade.closed", refetch);
  useAblyChannel("trading", "trade.exited_early", refetch);

  return (
    <section className={styles.container}>
      <p className={styles.title}>Past Closed Trades</p>
      {trades.length === 0 ? (
        <p className={styles.empty}>No closed trades yet.</p>
      ) : (
        <div className={styles.row} ref={rowRef}>
          {trades.map((trade) => (
            <TradeCard key={trade.trade_id} trade={trade} isNew={flashIds.has(trade.trade_id)} />
          ))}
          {isLoadingMore && <div className={styles.loadingMore}>Loading…</div>}
        </div>
      )}
    </section>
  );
}
