import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const text = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-text",
});
const figure = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-figure",
});

export const metadata: Metadata = {
  title: "ACME compensation",
  description: "Salary management for ACME",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${text.variable} ${figure.variable}`}>
      <body>
        <header className="border-b border-rule">
          <div className="mx-auto flex max-w-5xl items-baseline gap-6 px-6 py-5">
            <Link href="/" className="font-medium">
              ACME compensation
            </Link>
            <span className="text-sm text-muted">People and pay</span>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
