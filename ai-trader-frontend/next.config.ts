import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: [
    "@aws-sdk/client-s3",
    "@aws-sdk/client-dynamodb",
    "@aws-sdk/lib-dynamodb",
    "@aws-sdk/s3-request-presigner",
  ],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "auto-ai-trader-charts.s3.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "auto-ai-trader-charts.s3.*.amazonaws.com",
      },
    ],
  },
};

export default nextConfig;
