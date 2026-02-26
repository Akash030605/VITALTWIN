"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { gsap } from "gsap";

export default function ResultsPage() {
  const pageRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const linkRef = useRef(null);

  useEffect(() => {
    if (!pageRef.current) return;
    gsap.fromTo(titleRef.current, { opacity: 0, y: 24, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 1, ease: "power3.out" });
    gsap.fromTo(subtitleRef.current, { opacity: 0 }, { opacity: 1, duration: 0.8, delay: 0.35, ease: "power2.out" });
    gsap.fromTo(linkRef.current, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.6, delay: 0.7, ease: "power3.out" });
  }, []);

  return (
    <div ref={pageRef} className="min-h-screen flex flex-col items-center justify-center px-6">
      <p ref={titleRef} className="font-mono text-[var(--color-primary)] text-glow text-center text-lg tracking-wider mb-6">
        Report generated.
      </p>
      <p ref={subtitleRef} className="text-[var(--color-muted)] text-center text-sm mb-8">
        Your digital twin assessment is ready.
      </p>
      <Link
        ref={linkRef}
        href="/"
        className="rounded-lg bg-[var(--color-primary)] px-6 py-3 font-heading text-sm font-semibold uppercase tracking-wider text-[var(--background)] hover:opacity-90"
      >
        Back to lab
      </Link>
    </div>
  );
}
