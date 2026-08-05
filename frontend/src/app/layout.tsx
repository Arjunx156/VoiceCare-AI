import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import BackendWarmup from "@/components/BackendWarmup";

// Backend origin (Render) — known at build time on Vercel. Used to preconnect
// so the first API/WS call skips DNS + TCP + TLS setup.
const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_URL;

// Geist over Inter. Inter is the face every generated dashboard defaults to;
// Geist is drawn for the same job with more shape in the letterforms, and it
// holds up better at the heavy display weights this dark theme needs.
const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

// Numbers only: counts, IDs, timestamps, latencies. Not labels — see the
// font note in globals.css.
const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const companyName = process.env.NEXT_PUBLIC_COMPANY_NAME || "CommerceMind";
const appName = process.env.NEXT_PUBLIC_APP_NAME || "VoiceCare AI";

export const metadata: Metadata = {
  title: `${companyName} ${appName} — Voice-First Customer Support`,
  description:
    "Speak your language, get resolved instantly. AI-powered voice support across 8 Indian languages for e-commerce.",
  keywords: [
    "voice support",
    "AI customer service",
    "multilingual",
    "e-commerce",
    "India",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {/* React 19 hoists resource links into <head> */}
        {backendOrigin && (
          <>
            <link rel="preconnect" href={backendOrigin} crossOrigin="anonymous" />
            <link rel="dns-prefetch" href={backendOrigin} />
          </>
        )}
        <BackendWarmup />
        {children}
      </body>
    </html>
  );
}
