"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/body-ageing", label: "Body Ageing" },
  { href: "/organs", label: "Organs" },
  { href: "/recommendations", label: "Recommendations" },
];

export default function DashboardNav({ className = "" }) {
  const pathname = usePathname();

  return (
    <nav
      className={`flex items-center gap-6 overflow-x-auto overflow-y-hidden min-h-0 ${className}`}
      aria-label="Main sections"
    >
      {LINKS.map(({ href, label }) => {
        const isActive = pathname === href || (href !== "/" && pathname?.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={`
              text-sm font-medium whitespace-nowrap py-2 transition-colors duration-150
              border-0 outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)] rounded-sm
              ${isActive
                ? "text-[var(--color-primary)]"
                : "text-[var(--color-muted)] hover:text-[var(--foreground)]"
              }
            `}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
