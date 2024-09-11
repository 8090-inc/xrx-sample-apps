import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SkinConfigurations } from "./types/skinConfig";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Patient Information Intake",
  description: "Patient Information Intake System"
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const skinConfig = SkinConfigurations["patient-information-agent"];

  return (
    <html lang="en">
      <head>
        <style>{`
          :root {
            --background-color: ${skinConfig.styles.backgroundColor};
            --secondary-color: ${skinConfig.styles.secondaryColor};
            --main-font: ${skinConfig.styles.mainFont};
            --logo-background-color: ${skinConfig.styles.logoBackgroundColor};
            --font-color-on-background: ${skinConfig.styles.fontColorOnBackground};
            --speaking-pulse-color: ${skinConfig.styles.speakingPulseColor};
            --thinking-color: ${skinConfig.styles.thinkingColor};
          }
        `}</style>
      </head>
      <body
        className={`${inter.className} min-h-screen flex items-center justify-center `}
      >
        {children}
      </body>
    </html>
  );
}

// This is the root layout component for your Next.js app.
// Learn more: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts#root-layout-required
