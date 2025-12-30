import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF Intelligence Assistant",
  description: "Enterprise-grade AI-powered PDF document assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}

