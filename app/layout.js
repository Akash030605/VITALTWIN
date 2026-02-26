import { Poppins, DM_Sans } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";
import PageBackground from "../components/ui/PageBackground";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "VitalTwin | Your Health Digital Twin",
  description: "See how your lifestyle choices affect your organs over time.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${poppins.variable} ${dmSans.variable} ${geistMono.variable} antialiased`}
        suppressHydrationWarning
      >
        <PageBackground />
        {children}
      </body>
    </html>
  );
}
