import { Poppins } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";
import PageBackground from "../components/ui/PageBackground";
import LenisProvider from "../components/ui/LenisProvider";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
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
        className={`${poppins.variable} ${geistMono.variable} antialiased`}
        suppressHydrationWarning
      >
        <LenisProvider>
          <PageBackground />
          {children}
        </LenisProvider>
      </body>
    </html>
  );
}
