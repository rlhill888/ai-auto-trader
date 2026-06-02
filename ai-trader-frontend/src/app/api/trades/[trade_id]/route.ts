import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ trade_id: string }> }
) {
  const { trade_id } = await params;

  const { data, error } = await supabase
    .from("trade_decisions")
    .select("*")
    .eq("trade_id", trade_id)
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 404 });

  return NextResponse.json(data);
}
