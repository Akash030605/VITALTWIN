"use client";

import { useRef, useEffect, Suspense } from "react";
import dynamic from "next/dynamic";
import { gsap } from "gsap";

const Canvas = dynamic(
  () => import("@react-three/fiber").then((m) => m.Canvas),
  { ssr: false }
);
const HeartModelSceneCinematic = dynamic(
  () => import("./three/HeartModelSceneCinematic").then((m) => m.default),
  { ssr: false }
);

const STEPS = [
  "Initializing digital twin...",
  "Calibrating vitals...",
  "Running lifestyle projections...",
  "Building your report...",
];

export default function DigitalTwinLoadingScene({ onComplete }) {
  const overlayRef = useRef(null);
  const modelWrapRef = useRef(null);
  const stepsRef = useRef([]);
  const progressRef = useRef(null);
  const progressFillRef = useRef(null);
  const readyRef = useRef(null);
  const sweepRef = useRef(null);

  useEffect(() => {
    if (!overlayRef.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        onComplete: () => {
          gsap.to(overlayRef.current, { opacity: 0, duration: 0.9, ease: "power2.in" });
          gsap.delayedCall(0.95, () => onComplete?.());
        },
      });

      // Entry: overlay and model fade in
      tl.set(overlayRef.current, { opacity: 0 });
      tl.set(stepsRef.current, { opacity: 0, y: 12 });
      tl.set(progressFillRef.current, { scaleX: 0 });
      tl.set(readyRef.current, { opacity: 0, scale: 0.9 });
      tl.set(sweepRef.current, { yPercent: -20 });

      tl.to(overlayRef.current, { opacity: 1, duration: 0.6, ease: "power2.out" });
      tl.fromTo(
        modelWrapRef.current,
        { scale: 0.92, opacity: 0.3 },
        { scale: 1, opacity: 1, duration: 1.2, ease: "power3.out" },
        "-=0.3"
      );

      // Staggered step lines
      stepsRef.current.forEach((el, i) => {
        if (!el) return;
        const pos = 0.5 + i * 0.4;
        tl.to(el, { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }, pos);
        if (i > 0) tl.to(stepsRef.current[i - 1], { opacity: 0.45 }, pos - 0.05);
      });

      // Progress bar fill (smooth over 2s)
      tl.to(progressFillRef.current, { scaleX: 1, duration: 2, ease: "power2.inOut" }, 1.2);

      // Sweep line animation (continuous feel)
      tl.to(sweepRef.current, { yPercent: 120, duration: 2.5, ease: "none" }, 0.8);

      // "Ready" reveal
      tl.to(readyRef.current, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.2)" }, 3.4);
      tl.to(readyRef.current, { textShadow: "0 0 30px rgba(20,184,166,0.6)", duration: 0.3 }, 3.9);

      // Hold then exit
      tl.to({}, { duration: 1.2 }, 4.2);
    }, overlayRef);

    return () => ctx.revert();
  }, [onComplete]);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[var(--color-bg)] overflow-hidden"
      aria-live="polite"
      aria-label="Loading digital twin report"
    >
      {/* 3D model background */}
      <div
        ref={modelWrapRef}
        className="absolute inset-0 opacity-90"
      >
        <Canvas
          camera={{ position: [0, 0, 14], fov: 70 }}
          gl={{ antialias: true, alpha: true }}
          className="w-full h-full"
        >
          <Suspense fallback={null}>
            <HeartModelSceneCinematic />
          </Suspense>
        </Canvas>
      </div>

      {/* Dark overlay so text is readable */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(180deg, rgba(8,10,13,0.7) 0%, rgba(8,10,13,0.85) 50%, rgba(8,10,13,0.95) 100%)",
        }}
      />
      {/* Vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 80% 80% at 50% 50%, transparent 50%, rgba(0,0,0,0.6) 100%)",
        }}
      />
      {/* Scan sweep */}
      <div
        ref={sweepRef}
        className="absolute left-0 right-0 h-[2px] pointer-events-none z-10"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(20,184,166,0.6) 50%, transparent 100%)",
          boxShadow: "0 0 20px rgba(20,184,166,0.4)",
        }}
      />
      {/* Scan line */}
      <div className="absolute inset-0 pointer-events-none scan-line opacity-40" aria-hidden />

      {/* Content */}
      <div className="relative z-10 w-full max-w-md px-6 flex flex-col items-center">
        <p className="font-mono text-[10px] text-[var(--color-primary)]/80 tracking-[0.2em] uppercase mb-8">
          VitalTwin · Generating report
        </p>

        <div className="w-full space-y-3 mb-10">
          {STEPS.map((label, i) => (
            <p
              key={i}
              ref={(el) => { stepsRef.current[i] = el; }}
              className="font-mono text-sm text-[var(--color-primary)]/90 tracking-wide"
            >
              {label}
            </p>
          ))}
        </div>

        {/* Progress bar */}
        <div ref={progressRef} className="w-full h-1 rounded-full bg-[var(--color-surface)]/80 overflow-hidden mb-2">
          <div
            ref={progressFillRef}
            className="h-full rounded-full bg-[var(--color-primary)] origin-left"
            style={{ width: "100%" }}
          />
        </div>
        <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase tracking-wider mb-12">
          Analysis in progress
        </p>

        <p
          ref={readyRef}
          className="font-heading text-xl font-semibold tracking-tight text-[var(--color-primary)] text-glow"
        >
          Report ready.
        </p>
      </div>
    </div>
  );
}
