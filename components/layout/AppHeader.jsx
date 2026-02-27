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

  return (
    <header className="sticky top-0 z-40 h-14 flex items-center border-b border-white/10 bg-[var(--color-bg)]/90 backdrop-blur-sm">
      <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between gap-6">
        <Link
          href="/"
          className="shrink-0 font-semibold text-[var(--color-primary)] text-base tracking-tight hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] rounded"
          aria-label="VitalTwin home"
        >
          VitalTwin
        </Link>

        {showDashboardNav ? (
          <>
            <DashboardNav className="flex-1 justify-center min-w-0 max-w-md" />
            <div className="relative shrink-0">
              <button
                ref={profileAnchorRef}
                type="button"
                onClick={() => setProfileOpen((o) => !o)}
                className="p-2 rounded text-[var(--color-muted)] hover:text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] transition-colors"
                aria-label="View profile"
                aria-expanded={profileOpen}
                aria-haspopup="dialog"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 14a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
                  <path d="M6 20c0-3 3-4 6-4s6 1 6 4" />
                </svg>
              </button>
              <ProfilePopup
                profile={profile}
                open={profileOpen}
                onClose={() => setProfileOpen(false)}
                anchorRef={profileAnchorRef}
              />
            </div>
          </>
        ) : (
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-[var(--color-muted)] font-medium hover:text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] rounded py-2 px-2"
              aria-label="Fill profile"
            >
              Fill profile
            </Link>
            <Link
              href="/health-questions"
              className="text-sm font-medium text-[var(--color-primary)] hover:underline focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] rounded py-2 px-2"
              aria-label="Start assessment"
            >
              Start assessment
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
