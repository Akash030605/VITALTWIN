"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect } from "react";
import { gsap } from "gsap";

const HumanModelView = dynamic(() => import("../HumanModelView"), { ssr: false });

const TAGLINES = [
  "Digital twin initialized.",
  "Anatomical model loaded.",
  "Your profile. Your prediction.",
];

export default function HeroWithModel({ onAnimationsReady }) {
  const containerRef = useRef(null);
  const modelWrapRef = useRef(null);
  const line1Ref = useRef(null);
  const line2Ref = useRef(null);
  const line3Ref = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(modelWrapRef.current, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 1.4, ease: "power3.out" });
      gsap.fromTo(line1Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 0.6, ease: "power3.out" });
      gsap.fromTo(line2Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 1, ease: "power3.out" });
      gsap.fromTo(line3Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 1.4, ease: "power3.out" });
      if (onAnimationsReady) gsap.delayedCall(1.6, onAnimationsReady);
    }, containerRef);
    return () => ctx.revert();
  }, [onAnimationsReady]);

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[50vh] lg:min-h-[calc(100vh-4rem)]">
      <div ref={modelWrapRef} className="relative overflow-hidden w-full h-full min-h-[420px]">
        <HumanModelView className="w-full h-full min-h-0" />
        <div className="absolute inset-0 pointer-events-none scan-line opacity-25" aria-hidden />
        <div className="absolute inset-0 cinematic-spotlight" aria-hidden />
      </div>
      <div className="absolute bottom-6 left-6 space-y-1 font-mono text-xs text-[var(--color-primary)]/90 tracking-wide">
        <p ref={line1Ref} className="text-[var(--color-primary)] text-glow">{TAGLINES[0]}</p>
        <p ref={line2Ref} className="text-[var(--color-primary)]/80">{TAGLINES[1]}</p>
        <p ref={line3Ref} className="text-[var(--color-muted)] text-[11px]">{TAGLINES[2]}</p>
      </div>
    </div>
  );
}
