import styles from "./OngoingTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { getTrades } from "@/lib/api";

export default async function OngoingTrades() {
  const liveTrades = await getTrades("open");

  return (
    <section className={styles.container}>
      <p className={styles.title}>Ongoing Trades</p>
      {liveTrades.length === 0 ? (
        <p className={styles.empty}>No active trades.</p>
      ) : (
        <div className={styles.row}>
          {liveTrades.map((trade) => (
            <TradeCard key={trade.trade_id} trade={trade} live />
          ))}
        </div>
      )}
    </section>
  );
}
