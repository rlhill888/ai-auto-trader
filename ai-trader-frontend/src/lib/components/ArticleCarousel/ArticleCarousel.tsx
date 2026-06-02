"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import styles from "./ArticleCarousel.module.css";
import { Trade } from "@/lib/types";
import parse, { domToReact, DOMNode, Element } from "html-react-parser";

const summaryParseOptions = {
  replace(node: DOMNode) {
    if (node instanceof Element && node.name === "a") {
      return <span>{domToReact(node.children as DOMNode[], summaryParseOptions)}</span>;
    }
  },
};

const INTERVAL_MS = 4000;

export default function ArticleCarousel({ trades }: { trades: Trade[] }) {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState<"right" | "left">("right");
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const startInterval = () => {
    clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      setDirection("right");
      setIndex((i) => (i + 1) % trades.length);
    }, INTERVAL_MS);
  };

  useEffect(() => {
    startInterval();
    return () => clearInterval(intervalRef.current);
  }, [trades.length]);

  const next = () => {
    clearInterval(intervalRef.current);
    setDirection("right");
    setIndex((i) => (i + 1) % trades.length);
  };

  const prev = () => {
    clearInterval(intervalRef.current);
    setDirection("left");
    setIndex((i) => (i - 1 + trades.length) % trades.length);
  };

  if (trades.length === 0) return null;

  const article = trades[index];

  const formatted = new Date(article.timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const badgeClass =
    article.trade_status === "skipped"
      ? styles.skipped
      : article.direction === "buy"
      ? styles.buy
      : styles.sell;

  const badgeLabel =
    article.trade_status === "skipped" ? "skipped" : article.direction;

  return (
    <div className={styles.container}>
      <p className={styles.title}>Recent Articles</p>

      <div className={styles.cardWrapper}>
        <Link
          key={index}
          href={`/trades/${article.trade_id}`}
          className={`${styles.card} ${direction === "right" ? styles.slideFromRight : styles.slideFromLeft}`}
        >
          <p className={styles.cardTitle}>{article.article_title}</p>
          <div className={styles.cardSummary}>{parse(article.article_summary, summaryParseOptions)}</div>
          <div className={styles.meta}>
            <span className={`${styles.badge} ${badgeClass}`}>{badgeLabel}</span>
            <span className={styles.instrument}>{article.instrument.replace("_", "/")}</span>
          </div>
          <p className={styles.timestamp}>{formatted}</p>
        </Link>
      </div>

      <div className={styles.nav}>
        <button className={styles.navBtn} onClick={prev} aria-label="Previous">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <span className={styles.counter}>{index + 1} / {trades.length}</span>
        <button className={styles.navBtn} onClick={next} aria-label="Next">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>
      </div>
    </div>
  );
}
