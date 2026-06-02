import Link from "next/link";
import styles from "./AccountSummary.module.css";
import { getAccountNav, getDailyMoneyMade } from "@/lib/api";

export default async function AccountSummary() {
  const [nav, dailyMoneyMade] = await Promise.all([getAccountNav(), getDailyMoneyMade()]);

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
      <Link href="/trades" className={styles.tradesButton}>
        View all trades →
      </Link>
    </section>
  );
}
