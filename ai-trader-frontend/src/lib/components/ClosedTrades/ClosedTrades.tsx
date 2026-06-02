import styles from "./ClosedTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { getTrades } from "@/lib/api";

export default async function ClosedTrades() {
  const closedTrades = await getTrades("closed");

  return (
    <section className={styles.container}>
      <p className={styles.title}>Past Closed Trades</p>
      {closedTrades.length === 0 ? (
        <p className={styles.empty}>No closed trades yet.</p>
      ) : (
        <div className={styles.row}>
          {closedTrades.map((trade) => (
            <TradeCard key={trade.trade_id} trade={trade} />
          ))}
        </div>
      )}
    </section>
  );
}
