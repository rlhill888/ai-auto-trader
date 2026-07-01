import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
