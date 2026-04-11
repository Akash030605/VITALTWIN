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

  const initials = profile?.name
    ? profile.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "?";

  return (
    <header
      className="sticky top-0 z-40"
      style={{
        background: "rgba(255,255,255,0.88)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        borderBottom: "1px solid rgba(5,150,105,0.12)",
        boxShadow: "0 1px 3px rgba(15,23,42,0.06), 0 4px 12px rgba(5,150,105,0.04)",
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">

        {/* Wordmark */}
        <Link
          href="/"
          className="shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/30 rounded"
          aria-label="VitalTwin home"
        >
          <span className="text-[15px] font-bold tracking-tight select-none">
            <span className="text-(--color-primary)">Vital</span>
            <span className="text-slate-900">Twin</span>
          </span>
        </Link>

        {/* Center nav — only when a report exists */}
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
                className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary)/30"
                aria-label="View profile"
                aria-expanded={profileOpen}
                aria-haspopup="dialog"
              >
                <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                  <span className="text-[10px] font-bold text-(--color-primary)">{initials}</span>
                </div>
                <span className="text-sm font-medium text-slate-700 hidden md:block max-w-[6rem] truncate leading-none">
                  {profile?.name ?? "Profile"}
                </span>
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>
              <ProfilePopup
                profile={profile}
                open={profileOpen}
                onClose={() => setProfileOpen(false)}
                anchorRef={profileAnchorRef}
              />
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Link
                href="/"
                className="text-sm font-medium text-slate-500 hover:text-slate-800 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
              >
                Home
              </Link>
              <Link
                href="/health-questions"
                className="text-sm font-semibold text-white bg-(--color-primary) hover:bg-(--color-primary-deep) px-4 py-1.5 rounded-lg transition-colors"
                style={{ boxShadow: "0 2px 8px rgba(5,150,105,0.25)" }}
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Mobile nav strip */}
      {showDashboardNav && (
        <div className="sm:hidden border-t border-slate-100 px-4 py-2">
          <DashboardNav />
        </div>
      )}
    </header>
  );
}
