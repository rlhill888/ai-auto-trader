import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { getWeeklyAnalysis, getWeeklyCharts } from "@/lib/api";
import ChartCarousel from "./ChartCarousel";
import styles from "./page.module.css";

function formatDateRange(weekStart: string, weekEnd: string): string {
  const start = new Date(weekStart);
  const end = new Date(weekEnd);
  const opts: Intl.DateTimeFormatOptions = { month: "long", day: "numeric" };
  return `${start.toLocaleDateString("en-US", opts)} – ${end.toLocaleDateString("en-US", { ...opts, year: "numeric" })}`;
}

export default async function WeeklyAnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const report = await getWeeklyAnalysis(id);

  if (!report) notFound();

  const charts = await getWeeklyCharts(report.week_start, report.week_end);

  const dateRange = formatDateRange(report.week_start, report.week_end);

  const sections: { label: string; content: string }[] = [
    { label: "Synopsis", content: report.synopsis },
    { label: "Key Insights", content: report.key_insights },
    { label: "Biggest Mistakes", content: report.biggest_mistakes },
    { label: "Best Performing Themes", content: report.best_performing_themes },
    { label: "Next Week Playbook", content: report.new_playbook_rules },
  ].filter((s) => s.content?.trim());

  return (
    <main style={{ minHeight: "100vh", background: "#ffffff" }}>
      <div className={styles.container}>
        <div className={styles.topBar}>
          <Link href="/" className={styles.back}>
            ← Back to dashboard
          </Link>
        </div>

        <div className={styles.header}>
          <p className={styles.eyebrow}>Weekly Analysis Report</p>
          <h1 className={styles.title}>{dateRange}</h1>
          <div className={styles.meta}>
            <span className={styles.badge}>{report.trade_count} trades analyzed</span>
          </div>
        </div>

        {sections.map(({ label, content }) => (
          <div key={label} className={styles.card}>
            <p className={styles.sectionLabel}>{label}</p>
            <div className={styles.body}>
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        ))}

        {charts.length > 0 && (
          <div className={styles.card}>
            <p className={styles.sectionLabel}>Data Visualization</p>
            <ChartCarousel charts={charts} />
          </div>
        )}
      </div>
    </main>
  );
}
