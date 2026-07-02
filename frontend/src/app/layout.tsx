import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

// Display face for hero + section headlines. Geometric, techy, premium on dark;
// pairs cleanly with Inter body. Swap here (e.g. Fraunces) to change the whole
// display voice in one place — everything else reads --font-display.
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
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
      <body className={`${inter.variable} ${spaceGrotesk.variable} antialiased`}>{children}</body>
    </html>
  );
}
