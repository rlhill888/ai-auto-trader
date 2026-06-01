"use client";

import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import styles from "./ChartCarousel.module.css";
import { mockTrades } from "@/lib/mockTrades";

const COLORS = ["#4ade80", "#f87171", "#facc15", "#60a5fa"];

function buildChartData() {
  const winLoss = [
    { name: "Wins", value: mockTrades.filter((t) => t.is_good_trade).length },
    { name: "Skipped", value: mockTrades.filter((t) => !t.is_good_trade).length },
  ];

  const byInstrument = Object.values(
    mockTrades.reduce<Record<string, { instrument: string; trades: number }>>((acc, t) => {
      const key = t.instrument.replace("_", "/");
      acc[key] = acc[key] ?? { instrument: key, trades: 0 };
      acc[key].trades += 1;
      return acc;
    }, {})
  );

  const confidence = mockTrades
    .filter((t) => t.trade_status !== "skipped")
    .map((t) => ({
      name: t.instrument.replace("_", "/"),
      confidence: Math.round(t.confidence * 100),
    }));

  const byDirection = [
    { name: "Buy", units: mockTrades.filter((t) => t.direction === "buy").reduce((s, t) => s + t.units, 0) },
    { name: "Sell", units: mockTrades.filter((t) => t.direction === "sell").reduce((s, t) => s + t.units, 0) },
  ];

  return { winLoss, byInstrument, confidence, byDirection };
}

const { winLoss, byInstrument, confidence, byDirection } = buildChartData();

const TOOLTIP_STYLE = {
  backgroundColor: "#ffffff",
  border: "1px solid #ebebeb",
  borderRadius: "6px",
  color: "#0a0a0a",
  fontSize: "12px",
};

type SlideConfig = { title: string; key: string };

const slideConfigs: SlideConfig[] = [
  { title: "Win / Skip Ratio", key: "winLoss" },
  { title: "Trades by Instrument", key: "byInstrument" },
  { title: "Confidence by Trade", key: "confidence" },
  { title: "Units by Direction", key: "byDirection" },
];

function SlideChart({ slideKey }: { slideKey: string }) {
  if (slideKey === "winLoss") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={winLoss} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius="60%" label={({ name, value }) => `${name}: ${value}`}>
            {winLoss.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  if (slideKey === "byInstrument") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={byInstrument} margin={{ left: -20, bottom: 0 }}>
          <XAxis dataKey="instrument" tick={{ fill: "#999", fontSize: 10 }} />
          <YAxis tick={{ fill: "#999", fontSize: 10 }} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Bar dataKey="trades" fill="#4ade80" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }
  if (slideKey === "confidence") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={confidence} margin={{ left: -20, bottom: 0 }}>
          <XAxis dataKey="name" tick={{ fill: "#999", fontSize: 10 }} />
          <YAxis domain={[0, 100]} tick={{ fill: "#999", fontSize: 10 }} unit="%" />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "Confidence"]} />
          <Bar dataKey="confidence" fill="#60a5fa" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={byDirection} margin={{ left: -20, bottom: 0 }}>
        <XAxis dataKey="name" tick={{ fill: "#999", fontSize: 10 }} />
        <YAxis tick={{ fill: "#999", fontSize: 10 }} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Bar dataKey="units" radius={[4, 4, 0, 0]}>
          {byDirection.map((entry, i) => (
            <Cell key={i} fill={entry.name === "Buy" ? "#4ade80" : "#f87171"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function ChartCarousel() {
  const [index, setIndex] = useState(0);

  return (
    <section className={styles.container}>
      <p className={styles.title}>Performance Charts</p>
      <div className={styles.carousel}>
        <div className={styles.slide}>
          <p className={styles.slideTitle}>{slideConfigs[index].title}</p>
          <div style={{ flex: 1, minHeight: 0 }}>
            <SlideChart slideKey={slideConfigs[index].key} />
          </div>
        </div>
        <div className={styles.nav}>
          <button className={styles.navBtn} onClick={() => setIndex((i) => (i - 1 + slideConfigs.length) % slideConfigs.length)}>‹</button>
          <div className={styles.dots}>
            {slideConfigs.map((_, i) => (
              <div key={i} className={`${styles.dot} ${i === index ? styles.dotActive : ""}`} />
            ))}
          </div>
          <button className={styles.navBtn} onClick={() => setIndex((i) => (i + 1) % slideConfigs.length)}>›</button>
        </div>
      </div>
    </section>
  );
}
