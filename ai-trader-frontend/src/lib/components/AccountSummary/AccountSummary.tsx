import Link from "next/link";
import styles from "./AccountSummary.module.css";
import { getAccountNav, getDailyStats } from "@/lib/api";

export default async function AccountSummary() {
  const [nav, daily] = await Promise.all([getAccountNav(), getDailyStats()]);

  const { dailyMoneyMade, tradesCompleted, succeeded, failed } = daily;
  const isPositive = dailyMoneyMade >= 0;

  return (
    <section className={styles.container}>
      <div>
        <p className={styles.label}>Account Balance</p>
        <h1 className={styles.balance}>
          ${nav.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </h1>
        <p className={`${styles.profit} ${isPositive ? styles.positive : styles.negative}`}>
          {isPositive ? "+" : "-"}${Math.abs(dailyMoneyMade).toFixed(2)} today
        </p>
      </div>
      <div className={styles.right}>
        <Link href="/trades" className={styles.tradesButton}>
          View all trades →
        </Link>
        {tradesCompleted > 0 && (
          <div className={styles.dailyStats}>
            <span className={styles.statsTotal}>{tradesCompleted} trade{tradesCompleted !== 1 ? "s" : ""} today</span>
            <div className={styles.statsBreakdown}>
              <span className={styles.statsSucceeded}>{succeeded} succeeded</span>
              <span className={styles.statsFailed}>{failed} failed</span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
