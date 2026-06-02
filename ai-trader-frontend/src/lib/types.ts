export type Trade = {
  trade_id: string;
  article_id: string;
  article_title: string;
  article_summary: string;
  is_good_trade: boolean;
  instrument: string;
  direction: string;
  units: number;
  reasoning: string;
  confidence: number;
  timestamp: string;
  oanda_order_id: string;
  oanda_trade_id: string;
  trade_status: "open" | "closed" | "skipped";
  is_successful?: boolean;
  lesson_learned?: string;
};
