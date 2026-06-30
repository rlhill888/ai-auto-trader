import { GetObjectCommand, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { NextResponse } from "next/server";
import { s3 } from "@/lib/s3";

const BUCKET = "auto-ai-trader-charts";
const PRESIGN_EXPIRES_SECONDS = 3600;

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const weekStart = searchParams.get("week_start");
  const weekEnd = searchParams.get("week_end");

  if (!weekStart || !weekEnd) {
    return NextResponse.json({ error: "week_start and week_end are required" }, { status: 400 });
  }

  const prefix = `${weekStart}_to_${weekEnd}/`;

  try {
    const list = await s3.send(
      new ListObjectsV2Command({ Bucket: BUCKET, Prefix: prefix })
    );

    const keys = (list.Contents ?? [])
      .map((obj) => obj.Key!)
      .filter(Boolean)
      .sort();

    const urls = await Promise.all(
      keys.map((key) =>
        getSignedUrl(s3, new GetObjectCommand({ Bucket: BUCKET, Key: key }), {
          expiresIn: PRESIGN_EXPIRES_SECONDS,
        })
      )
    );

    return NextResponse.json({ charts: urls });
  } catch (err) {
    console.error("Failed to list charts from S3:", err);
    return NextResponse.json({ charts: [] });
  }
}
