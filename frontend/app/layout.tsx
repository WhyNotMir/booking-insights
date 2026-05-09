import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Booking Insights",
  description: "Journal entry insight dashboard"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
