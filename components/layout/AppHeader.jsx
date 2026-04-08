"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useStore } from "../../store/useStore";
import ProfilePopup from "../results/ProfilePopup";
import DashboardNav from "../results/DashboardNav";

export default function AppHeader() {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);
  const [mounted, setMounted] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileAnchorRef = useRef(null);

  useEffect(() => setMounted(true), []);

  const showDashboardNav = mounted && result;

  // Get initials for avatar
  const initials = profile?.name
    ? profile.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "?";

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/40 rounded" aria-label="VitalTwin home">
          <div className="w-7 h-7 rounded-lg bg-(--color-primary) flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
            </svg>
          </div>
          <span className="font-semibold text-slate-900 text-base">VitalTwin</span>
        </Link>

        {/* Dashboard nav — center */}
        {showDashboardNav && (
          <DashboardNav className="flex-1 justify-center hidden sm:flex" />
        )}

        {/* Right side */}
        <div className="flex items-center gap-2 shrink-0">
          {showDashboardNav ? (
            <div className="relative">
              <button
                ref={profileAnchorRef}
                type="button"
                onClick={() => setProfileOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/40"
                aria-label="View profile"
                aria-expanded={profileOpen}
                aria-haspopup="dialog"
              >
                <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                  <span className="text-[10px] font-bold text-(--color-primary)">{initials}</span>
                </div>
                <span className="text-sm font-medium text-slate-700 hidden md:block max-w-24 truncate">
                  {profile?.name ?? "Profile"}
                </span>
                <svg className="w-3.5 h-3.5 text-(--color-muted)" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>
              <ProfilePopup profile={profile} open={profileOpen} onClose={() => setProfileOpen(false)} anchorRef={profileAnchorRef} />
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link href="/" className="text-sm text-(--color-muted) hover:text-foreground font-medium rounded px-2 py-1.5 transition-colors">
                Home
              </Link>
              <Link href="/health-questions" className="text-sm font-semibold text-white bg-(--color-primary) hover:bg-(--color-primary-deep) px-4 py-1.5 rounded-lg transition-colors">
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Mobile nav — below header on dashboard */}
      {showDashboardNav && (
        <div className="sm:hidden border-t border-slate-100 px-4 py-2">
          <DashboardNav />
        </div>
      )}
    </header>
  );
}
