import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import BackendWarmup from "@/components/BackendWarmup";

// Backend origin (Render) — known at build time on Vercel. Used to preconnect
// so the first API/WS call skips DNS + TCP + TLS setup.
const backendOrigin = process.env.NEXT_PUBLIC_BACKEND_URL;

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

// The console's second register. Everything the pipeline produced —
// labels, ticket IDs, counts, latencies, status codes — is set in mono
// so it reads as machine output next to Inter's human prose. Only the
// three weights actually used are loaded.
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
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
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
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
