import Link from "next/link";
import { getTrades } from "@/lib/api";
import styles from "./page.module.css";
import TradeListClient from "./TradeListClient";

export default async function TradesPage() {
  const initialTrades = await getTrades(undefined, 40);

  return (
    <main style={{ minHeight: "100vh" }}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>
          ← Back to dashboard
        </Link>

        <div className={styles.header}>
          <h1 className={styles.title}>All Trades</h1>
          <p className={styles.subtitle}>Most recent trades</p>
        </div>

        <TradeListClient initialTrades={initialTrades} />
      </div>
    </main>
  );
}
