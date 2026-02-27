"use client";

import { useRef, useEffect, Suspense } from "react";
import dynamic from "next/dynamic";
import { gsap } from "gsap";

const Canvas = dynamic(
  () => import("@react-three/fiber").then((m) => m.Canvas),
  { ssr: false }
);
const BrainModelSceneCinematic = dynamic(
  () => import("./three/BrainModelSceneCinematic").then((m) => m.default),
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
  const progressFillRef = useRef(null);
  const percentRef = useRef(null);
  const readyRef = useRef(null);
  const sweepRef = useRef(null);
  const hudRef = useRef(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!overlayRef.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        onComplete: () => {
          gsap.to(overlayRef.current, { opacity: 0, duration: 0.9, ease: "power2.in" });
          gsap.delayedCall(0.95, () => onCompleteRef.current?.());
        },
      });

      // Entry: overlay and model fade in
      tl.set(overlayRef.current, { opacity: 0 });
      tl.set(stepsRef.current, { opacity: 0, y: 12 });
      tl.set(progressFillRef.current, { scaleX: 0 });
      tl.set(readyRef.current, { opacity: 0, scale: 0.9 });
      tl.set(sweepRef.current, { yPercent: -20 });
      tl.set(hudRef.current, { opacity: 0, scale: 0.95 });
      tl.set(percentRef.current, { textContent: "0" });

      tl.to(overlayRef.current, { opacity: 1, duration: 0.6, ease: "power2.out" });
      tl.to(hudRef.current, { opacity: 1, scale: 1, duration: 0.5, ease: "power2.out" }, 0.2);
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

      // Progress bar fill + percentage counter (2s)
      const proxy = { value: 0 };
      tl.to(proxy, { value: 100, duration: 2, ease: "power2.inOut", onUpdate: () => {
        if (percentRef.current) percentRef.current.textContent = String(Math.round(proxy.value));
      } }, 1.2);
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
  }, []);

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
            <BrainModelSceneCinematic />
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

      {/* Letterbox bars - cinematic */}
      <div className="absolute left-0 right-0 top-0 h-[6vh] bg-black/70 pointer-events-none z-10" aria-hidden />
      <div className="absolute left-0 right-0 bottom-0 h-[6vh] bg-black/70 pointer-events-none z-10" aria-hidden />

      {/* HUD-style content with corner brackets */}
      <div
        ref={hudRef}
        className="relative z-20 w-full max-w-lg mx-6 game-hud-frame rounded-sm border border-[var(--color-primary)]/40 bg-[var(--color-bg)]/60 backdrop-blur-sm px-8 py-10"
      >
        <p className="font-mono text-[10px] text-[var(--color-primary)]/90 tracking-[0.25em] uppercase mb-6">
          [ MISSION: GENERATE REPORT ]
        </p>

        <div className="w-full space-y-2.5 mb-8">
          {STEPS.map((label, i) => (
            <p
              key={i}
              ref={(el) => { stepsRef.current[i] = el; }}
              className="font-mono text-sm text-[var(--color-primary)]/90 tracking-wide"
            >
              <span className="text-[var(--color-muted)]/80 mr-2">[{i + 1}]</span>
              {label}
            </p>
          ))}
        </div>

        <div className="flex items-center gap-4 mb-2">
          <div className="flex-1 h-1.5 rounded-sm bg-[var(--color-surface)]/90 overflow-hidden border border-[var(--color-surface-border)]/50">
            <div
              ref={progressFillRef}
              className="h-full rounded-sm bg-[var(--color-primary)] origin-left"
              style={{ width: "100%" }}
            />
          </div>
          <span ref={percentRef} className="font-mono text-sm tabular-nums text-[var(--color-primary)] w-10 text-right">0</span>
          <span className="font-mono text-[10px] text-[var(--color-muted)] uppercase">%</span>
        </div>
        <p className="font-mono text-[10px] text-[var(--color-muted)] uppercase tracking-wider mb-10">
          System analysis in progress
        </p>

        <p
          ref={readyRef}
          className="font-heading text-xl font-semibold tracking-tight text-[var(--color-primary)] text-glow"
        >
          [ REPORT READY ]
        </p>
      </div>
    </div>
  );
}
