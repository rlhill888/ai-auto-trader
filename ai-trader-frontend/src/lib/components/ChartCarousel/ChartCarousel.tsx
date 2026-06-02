import styles from "./ChartCarousel.module.css";

export default function ChartCarousel() {
  return (
    <section className={styles.container}>
      <p className={styles.title}>Performance Charts</p>
      <div className={styles.placeholder}>
        <p className={styles.placeholderText}>Data analytics & visualization coming soon</p>
      </div>
    </section>
  );
}
