import Ably from "ably";
import { NextResponse } from "next/server";

export async function GET() {
  const client = new Ably.Rest(process.env.ABLY_API_KEY!);
  const tokenRequest = await client.auth.createTokenRequest({ clientId: "frontend" });
  return NextResponse.json(tokenRequest);
}
