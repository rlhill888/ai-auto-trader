import styles from "./ClosedTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { mockTrades } from "@/lib/mockTrades";

export default function ClosedTrades() {
  const closedTrades = mockTrades.filter((t) => t.trade_status === "closed");

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
