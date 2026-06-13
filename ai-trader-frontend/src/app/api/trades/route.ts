import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const status = searchParams.get("status");

  const limitParam = searchParams.get("limit");
  const offsetParam = searchParams.get("offset");

  let query = supabase
    .from("trade_decisions")
    .select("*")
    .order("timestamp", { ascending: false });

  if (status) query = query.eq("trade_status", status);

  if (limitParam) {
    const limit = parseInt(limitParam, 10);
    const offset = offsetParam ? parseInt(offsetParam, 10) : 0;
    query = query.range(offset, offset + limit - 1);
  }

  const { data, error } = await query;

  if (error) {
    console.log(error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
