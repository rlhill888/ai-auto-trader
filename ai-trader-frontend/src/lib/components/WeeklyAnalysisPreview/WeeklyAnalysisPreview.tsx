import Link from "next/link";
import { getLatestWeeklyAnalysis } from "@/lib/api";
import styles from "./WeeklyAnalysisPreview.module.css";

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`(.+?)`/g, "$1")
    .replace(/^[-*>]\s+/gm, "")
    .replace(/\n+/g, " ")
    .trim();
}

function formatDateRange(weekStart: string, weekEnd: string): string {
  const start = new Date(weekStart);
  const end = new Date(weekEnd);
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${start.toLocaleDateString("en-US", opts)} – ${end.toLocaleDateString("en-US", { ...opts, year: "numeric" })}`;
}

export default async function WeeklyAnalysisPreview() {
  const report = await getLatestWeeklyAnalysis();

  if (!report) {
    return (
      <section className={styles.container}>
        <p className={styles.title}>Weekly Analysis</p>
        <div className={styles.placeholder}>
          <p className={styles.placeholderText}>No weekly analysis yet</p>
        </div>
      </section>
    );
  }

  const excerpt = stripMarkdown(report.synopsis).slice(0, 160).trimEnd() + "…";
  const dateRange = formatDateRange(report.week_start, report.week_end);

  return (
    <section className={styles.container}>
      <p className={styles.title}>Weekly Analysis</p>
      <Link href={`/analysis/${report.id}`} className={styles.card}>
        <p className={styles.dateRange}>{dateRange}</p>
        <p className={styles.tradeCount}>{report.trade_count} trades analyzed</p>
        <p className={styles.excerpt}>{excerpt}</p>
        <div className={styles.vizPlaceholder}>
          <p className={styles.vizPlaceholderText}>Data Visualization Coming Soon</p>
        </div>
        <p className={styles.cta}>Read full analysis →</p>
      </Link>
    </section>
  );
}
