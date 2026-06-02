import styles from "./OngoingTrades.module.css";
import LiveTradesRow from "./LiveTradesRow";
import { getTrades } from "@/lib/api";

export default async function OngoingTrades() {
  const liveTrades = await getTrades("open");

  return (
    <section className={styles.container}>
      <p className={styles.title}>Ongoing Trades</p>
      {liveTrades.length === 0 ? (
        <p className={styles.empty}>No active trades.</p>
      ) : (
        <LiveTradesRow trades={liveTrades} />
      )}
    </section>
  );
}
