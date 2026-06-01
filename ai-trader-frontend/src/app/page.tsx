import AccountSummary from "@/lib/components/AccountSummary/AccountSummary";
import OngoingTrades from "@/lib/components/OngoingTrades/OngoingTrades";
import ChartCarousel from "@/lib/components/ChartCarousel/ChartCarousel";
import ClosedTrades from "@/lib/components/ClosedTrades/ClosedTrades";
import ArticleCarousel from "@/lib/components/ArticleCarousel/ArticleCarousel";

export default function Home() {
  return (
    <main style={{ color: "#000000", height: "100vh", overflow: "hidden", display: "flex" }}>

      {/* Left — fills height, sections split vertically */}
      <div style={{ width: "75%", borderRight: "1px solid #d2d2d7", height: "100%", display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0 }}>
          <AccountSummary />
        </div>
        <div style={{ flex: 1, minHeight: 0, borderBottom: "1px solid #d2d2d7" }}>
          <OngoingTrades />
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ClosedTrades />
        </div>
      </div>

      {/* Right — sticky sidebar, fills height */}
      <div style={{ width: "25%", height: "100%", overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ChartCarousel />
        </div>
        <div style={{ flexShrink: 0 }}>
          <ArticleCarousel />
        </div>
      </div>

    </main>
  );
}
