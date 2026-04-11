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
      tl.to(readyRef.current, { textShadow: "0 0 24px rgba(5,150,105,0.5)", duration: 0.3 }, 3.9);

      // Hold then exit
      tl.to({}, { duration: 1.2 }, 4.2);
    }, overlayRef);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-100 flex flex-col items-center justify-center bg-(--color-bg) overflow-hidden"
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

      {/* Light overlay — keeps 3D model visible while ensuring text readability */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(180deg, rgba(240,247,255,0.75) 0%, rgba(240,247,255,0.88) 50%, rgba(240,247,255,0.95) 100%)",
        }}
      />
      {/* Soft edge vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 80% 80% at 50% 50%, transparent 50%, rgba(5,150,105,0.06) 100%)",
        }}
      />
      {/* Scan sweep — sky blue */}
      <div
        ref={sweepRef}
        className="absolute left-0 right-0 h-0.5 pointer-events-none z-10"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(5,150,105,0.7) 50%, transparent 100%)",
          boxShadow: "0 0 16px rgba(5,150,105,0.35)",
        }}
      />
      {/* Scan line */}
      <div className="absolute inset-0 pointer-events-none scan-line opacity-30" aria-hidden />

      {/* Letterbox bars */}
      <div className="absolute left-0 right-0 top-0 h-[6vh] bg-emerald-50/80 pointer-events-none z-10 border-b border-emerald-100" aria-hidden />
      <div className="absolute left-0 right-0 bottom-0 h-[6vh] bg-emerald-50/80 pointer-events-none z-10 border-t border-emerald-100" aria-hidden />

      {/* Clinical analysis card */}
      <div
        ref={hudRef}
        className="relative z-20 w-full max-w-lg mx-6 rounded-2xl border border-emerald-200 bg-white/90 backdrop-blur-sm px-8 py-10 shadow-xl shadow-emerald-100/60"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-full bg-(--color-primary)/10 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-(--color-primary)" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" /></svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Generating your health report</p>
            <p className="text-xs text-(--color-muted)">AI analysis in progress — please wait</p>
          </div>
        </div>

        <div className="w-full space-y-2.5 mb-8">
          {STEPS.map((label, i) => (
            <div
              key={i}
              ref={(el) => { stepsRef.current[i] = el; }}
              className="flex items-center gap-2.5"
            >
              <div className="w-1.5 h-1.5 rounded-full bg-(--color-primary) shrink-0" aria-hidden />
              <p className="text-sm text-foreground/80">{label}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-4 mb-2">
          <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div
              ref={progressFillRef}
              className="h-full rounded-full bg-(--color-primary) origin-left"
              style={{ width: "100%" }}
            />
          </div>
          <span ref={percentRef} className="font-mono text-sm tabular-nums text-(--color-primary) w-10 text-right">0</span>
          <span className="text-xs text-(--color-muted)">%</span>
        </div>
        <p className="text-xs text-(--color-muted) mb-10">
          Analysing organ health, biological age, and risk factors…
        </p>

        <p
          ref={readyRef}
          className="font-heading text-xl font-semibold tracking-tight text-(--color-primary)"
        >
          Your report is ready
        </p>
      </div>
    </div>
  );
}
