import Link from "next/link";
import styles from "./AccountSummary.module.css";
import { getAccountNav, getDailyStats } from "@/lib/api";
import DailyStats from "./DailyStats";

export default async function AccountSummary() {
  const [nav, daily] = await Promise.all([getAccountNav(), getDailyStats()]);

  const isPositive = daily.dailyMoneyMade >= 0;

  return (
    <section className={styles.container}>
      <div>
        <p className={styles.label}>Account Balance</p>
        <h1 className={styles.balance}>
          ${nav.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </h1>
        <p className={`${styles.profit} ${isPositive ? styles.positive : styles.negative}`}>
          {isPositive ? "+" : "-"}${Math.abs(daily.dailyMoneyMade).toFixed(2)} today
        </p>
      </div>
      <div className={styles.right}>
        <Link href="/trades" className={styles.tradesButton}>
          View all trades →
        </Link>
        <DailyStats initialStats={daily} />
      </div>
    </section>
  );
}
