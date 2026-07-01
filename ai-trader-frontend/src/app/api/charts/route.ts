import { GetObjectCommand, HeadObjectCommand, ListObjectsV2Command } from "@aws-sdk/client-s3";
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

    const charts = await Promise.all(
      keys.map(async (key) => {
        const rawName = key.split("/").pop()?.replace(".png", "") ?? "";
        const [url, head] = await Promise.all([
          getSignedUrl(s3, new GetObjectCommand({ Bucket: BUCKET, Key: key }), {
            expiresIn: PRESIGN_EXPIRES_SECONDS,
          }),
          s3.send(new HeadObjectCommand({ Bucket: BUCKET, Key: key })),
        ]);
        const fallbackTitle = rawName.replace(/^\d+_/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        return {
          url,
          title: head.Metadata?.title ?? fallbackTitle,
          description: head.Metadata?.description ?? "",
        };
      })
    );

    return NextResponse.json({ charts });
  } catch (err) {
    console.error("Failed to list charts from S3:", err);
    return NextResponse.json({ charts: [] });
  }
}
