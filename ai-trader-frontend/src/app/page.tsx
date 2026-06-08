import AccountSummary from "@/lib/components/AccountSummary/AccountSummary";
import OngoingTrades from "@/lib/components/OngoingTrades/OngoingTrades";
import WeeklyAnalysisPreview from "@/lib/components/WeeklyAnalysisPreview/WeeklyAnalysisPreview";
import ClosedTrades from "@/lib/components/ClosedTrades/ClosedTrades";
import ArticleCarousel from "@/lib/components/ArticleCarousel/ArticleCarousel";
import { getTrades } from "@/lib/api";
import styles from "./page.module.css";

export default async function Home() {
  const [allTrades, openTrades, closedTrades] = await Promise.all([
    getTrades(),
    getTrades("open"),
    getTrades("closed"),
  ]);

  return (
    <main className={styles.main}>
      <div className={styles.left}>
        <div className={styles.leftTop}>
          <AccountSummary />
        </div>
        <div className={styles.leftMid}>
          <OngoingTrades initialTrades={openTrades} />
        </div>
        <div className={styles.leftBot}>
          <ClosedTrades initialTrades={closedTrades} />
        </div>
      </div>
      
      <div className={styles.right}>
        <div className={styles.rightTop}>
          <WeeklyAnalysisPreview />
        </div>
        <div className={styles.rightBot}>
          <ArticleCarousel trades={allTrades} />
        </div>
      </div>

    </main>
  );
}
