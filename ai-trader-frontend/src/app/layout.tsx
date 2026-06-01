import type { Metadata } from "next";
import "./globals.css";
import BackgroundAnimation from "@/lib/components/BackgroundAnimation/BackgroundAnimation";

export const metadata: Metadata = {
  title: "AI Trader",
  description: "Automated AI trading dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <BackgroundAnimation />
        <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
      </body>
    </html>
  );
}
