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
    <nav className={`flex items-center gap-0.5 ${className}`} aria-label="Dashboard sections">
      {LINKS.map(({ href, label }) => {
        const isActive = pathname === href || (href !== "/" && pathname?.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={`
              relative px-3.5 py-1.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/30
              ${isActive
                ? "text-(--color-primary-deep) bg-emerald-50 border border-emerald-100"
                : "text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-transparent"
              }
            `}
          >
            {isActive && (
              <span
                className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-(--color-primary)"
                aria-hidden
              />
            )}
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
