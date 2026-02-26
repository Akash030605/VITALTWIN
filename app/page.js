"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import HeroWithModel from "../components/landing/HeroWithModel";
import ProfileForm from "../components/landing/ProfileForm";

export default function StarterPage() {
  const pageRef = useRef(null);
  const titleRef = useRef(null);
  const heroRef = useRef(null);
  const formRef = useRef(null);

  const handleHeroReady = () => {
    if (formRef.current) {
      gsap.fromTo(formRef.current, { opacity: 0, y: 32 }, { opacity: 1, y: 0, duration: 1, ease: "power3.out" });
    }
  };

  useEffect(() => {
    if (!pageRef.current) return;
    gsap.fromTo(titleRef.current, { opacity: 0, y: -24 }, { opacity: 1, y: 0, duration: 1.1, ease: "power3.out" });
    gsap.fromTo(heroRef.current, { opacity: 0, scale: 0.98 }, { opacity: 1, scale: 1, duration: 1, delay: 0.15, ease: "power2.out" });
  }, []);

  return (
    <div ref={pageRef} className="min-h-screen relative flex flex-col">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/40 to-transparent" aria-hidden />

      <header className="sticky top-0 z-20 flex items-center justify-between gap-4 px-4 py-3 md:px-8 md:py-4 border-b border-[var(--color-surface-border)]/40 bg-[var(--color-bg)]/80 backdrop-blur-md">
        <Link
          href="/"
          ref={titleRef}
          className="font-heading text-lg md:text-xl font-semibold tracking-tighter text-[var(--foreground)] transition hover:text-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)] rounded"
        >
          VitalTwin
        </Link>
        <div className="flex items-center gap-6">
          <span className="hidden sm:inline font-mono text-[10px] md:text-xs text-[var(--color-muted)] tracking-[0.15em] uppercase">
            Digital twin · Healthcare forensics
          </span>
          <Link
            href="/health-questions"
            className="font-mono text-xs font-medium uppercase tracking-wider text-[var(--color-primary)] border border-[var(--color-primary)]/50 rounded px-4 py-2 transition hover:bg-[var(--color-primary)]/10 hover:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
          >
            Health assessment
          </Link>
        </div>
      </header>

      <main className="relative z-10 flex-1 grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-0 w-full max-w-7xl mx-auto min-h-0">
        <div ref={heroRef} className="min-h-[50vh] lg:min-h-[calc(100vh-4rem)] lg:border-r border-[var(--color-surface-border)]/40 bg-gradient-to-br from-[var(--color-surface)]/20 to-transparent">
          <HeroWithModel onAnimationsReady={handleHeroReady} />
        </div>
        <div ref={formRef} className="flex flex-col justify-center py-8 lg:py-12 lg:px-12">
          <ProfileForm />
        </div>
      </main>

      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/25 to-transparent" aria-hidden />
    </div>
  );
}
