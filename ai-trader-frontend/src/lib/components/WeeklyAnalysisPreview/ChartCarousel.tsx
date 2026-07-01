"use client";

import { useState, useEffect, useRef } from "react";
import { ChartItem } from "@/lib/api";
import styles from "./WeeklyAnalysisPreview.module.css";

export default function ChartCarousel({ charts }: { charts: ChartItem[] }) {
  const [index, setIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const resetTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % charts.length);
    }, 4000);
  };

  useEffect(() => {
    if (charts.length <= 1) return;
    resetTimer();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [charts.length]);

  if (charts.length === 0) return null;

  const current = charts[index];

  return (
    <div className={styles.carousel}>
      {current.title && <p className={styles.chartTitle}>{current.title}</p>}
      <div className={styles.carouselImgWrapper}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          key={index}
          src={current.url}
          alt={current.title}
          className={`${styles.carouselImg} ${styles.slideFromRight}`}
        />
      </div>
      {current.description && (
        <p className={styles.chartCaption}>{current.description}</p>
      )}
    </div>
  );
}
