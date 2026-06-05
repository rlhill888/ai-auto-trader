export type LiveTradeData = {
  unrealizedPl: number;
  entryPrice: number;
  tpPrice: number | null;
  slPrice: number | null;
};

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
  trade_status: "open" | "closed" | "skipped" | "already_in_trade";
  is_successful?: boolean;
  profit_loss?: number;
  exit_price?: number;
  lesson_learned?: string;
  left_trade_early?: boolean;
  reason_for_leaving_trade_early?: string;
};
