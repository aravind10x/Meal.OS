import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const sans = Manrope({
  variable: "--font-sans-ui",
  subsets: ["latin"],
});

const mono = IBM_Plex_Mono({
  variable: "--font-mono-ui",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Meal.OS",
  description: "AI meal operating system for Indian households",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#f3eee4",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${sans.variable} ${mono.variable} min-h-screen bg-background font-sans text-foreground antialiased md:pt-24`}
      >
        <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(91,140,127,0.18),transparent_28%),radial-gradient(circle_at_top_right,rgba(176,146,92,0.14),transparent_22%),linear-gradient(180deg,rgba(255,255,255,0.58),rgba(255,255,255,0))]" />
          <div className="absolute inset-x-0 top-0 h-64 bg-[linear-gradient(180deg,rgba(22,44,42,0.06),transparent)]" />
        </div>
        {children}
        <Toaster richColors position="top-center" />
      </body>
    </html>
  );
}
