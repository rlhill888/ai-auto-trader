import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET() {
  const { data, error } = await supabase
    .from("weekly_trading_reports")
    .select("*")
    .order("week_start", { ascending: false })
    .limit(1)
    .single();

  if (error) {
    if (error.code === "PGRST116") return NextResponse.json(null);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
