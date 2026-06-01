import styles from "./AccountSummary.module.css";

export default function AccountSummary() {
  const balance = 10482.50;
  const profit = 342.18;
  const isPositive = profit >= 0;

  return (
    <section className={styles.container}>
      <p className={styles.label}>Account Balance</p>
      <h1 className={styles.balance}>
        ${balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}
      </h1>
      <p className={`${styles.profit} ${isPositive ? styles.positive : styles.negative}`}>
        {isPositive ? "+" : "-"}${Math.abs(profit).toFixed(2)} today
      </p>
    </section>
  );
}
