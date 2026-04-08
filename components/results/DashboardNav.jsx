"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/body-ageing", label: "Body Ageing" },
  { href: "/organs", label: "Organs" },
  { href: "/recommendations", label: "Recommendations" },
];

export default function DashboardNav({ className = "" }) {
  const pathname = usePathname();
  return (
    <nav className={`flex items-center gap-1 ${className}`} aria-label="Dashboard sections">
      {LINKS.map(({ href, label }) => {
        const isActive = pathname === href || (href !== "/" && pathname?.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={`relative px-3 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/40 ${
              isActive
                ? "text-(--color-primary) bg-emerald-50"
                : "text-(--color-muted) hover:text-foreground hover:bg-slate-100"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
