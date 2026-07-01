"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import styles from "./ChartCarousel.module.css";

interface Chart {
  url: string;
  title?: string;
  description?: string;
}

const AUTO_INTERVAL = 4000;

export default function ChartCarousel({ charts }: { charts: Chart[] }) {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState<"next" | "prev">("next");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopAutoPlay = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startAutoPlay = useCallback(() => {
    if (charts.length <= 1) return;
    stopAutoPlay();
    intervalRef.current = setInterval(() => {
      setDirection("next");
      setIndex((i) => (i + 1) % charts.length);
    }, AUTO_INTERVAL);
  }, [charts.length]);

  useEffect(() => {
    startAutoPlay();
    return stopAutoPlay;
  }, [startAutoPlay]);

  if (charts.length === 0) return null;

  const prev = () => {
    stopAutoPlay();
    setDirection("prev");
    setIndex((i) => (i - 1 + charts.length) % charts.length);
  };

  const next = () => {
    stopAutoPlay();
    setDirection("next");
    setIndex((i) => (i + 1) % charts.length);
  };

  const goTo = (i: number) => {
    stopAutoPlay();
    setDirection(i > index ? "next" : "prev");
    setIndex(i);
  };

  const chart = charts[index];
  const slideClass = direction === "next" ? styles.slideFromRight : styles.slideFromLeft;

  return (
    <div className={styles.carousel}>
      <div className={styles.imageWrap}>
        <div key={index} className={`${styles.slide} ${slideClass}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={chart.url}
            alt={chart.title ?? "Chart"}
            className={styles.image}
          />
        </div>

        {charts.length > 1 && (
          <>
            <button className={`${styles.arrow} ${styles.arrowLeft}`} onClick={prev} aria-label="Previous chart">
              ‹
            </button>
            <button className={`${styles.arrow} ${styles.arrowRight}`} onClick={next} aria-label="Next chart">
              ›
            </button>
          </>
        )}
      </div>

      {(chart.title || chart.description) && (
        <div key={`body-${index}`} className={styles.body}>
          {chart.title && <p className={styles.title}>{chart.title}</p>}
          {chart.description && <p className={styles.description}>{chart.description}</p>}
        </div>
      )}

      {charts.length > 1 && (
        <div className={styles.dots}>
          {charts.map((_, i) => (
            <button
              key={i}
              className={`${styles.dot} ${i === index ? styles.dotActive : ""}`}
              onClick={() => goTo(i)}
              aria-label={`Go to chart ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
