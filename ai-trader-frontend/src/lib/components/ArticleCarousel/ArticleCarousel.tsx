"use client";

import { useState } from "react";
import Link from "next/link";
import styles from "./ArticleCarousel.module.css";
import { mockTrades } from "@/lib/mockTrades";

const articles = [...mockTrades]
  .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

export default function ArticleCarousel() {
  const [index, setIndex] = useState(0);
  const article = articles[index];

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

      <Link href={`/trades/${article.trade_id}`} className={styles.card}>
        <p className={styles.cardTitle}>{article.article_title}</p>
        <p className={styles.cardSummary}>{article.article_summary}</p>
        <div className={styles.meta}>
          <span className={`${styles.badge} ${badgeClass}`}>{badgeLabel}</span>
          <span className={styles.instrument}>{article.instrument.replace("_", "/")}</span>
        </div>
        <p className={styles.timestamp}>{formatted}</p>
      </Link>

      <div className={styles.nav}>
        <button
          className={styles.navBtn}
          onClick={() => setIndex((i) => (i - 1 + articles.length) % articles.length)}
        >
          ‹
        </button>
        <span className={styles.counter}>{index + 1} / {articles.length}</span>
        <button
          className={styles.navBtn}
          onClick={() => setIndex((i) => (i + 1) % articles.length)}
        >
          ›
        </button>
      </div>
    </div>
  );
}
