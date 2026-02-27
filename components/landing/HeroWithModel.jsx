"use client";

import dynamic from "next/dynamic";
import { useRef, useEffect, useState, useCallback } from "react";
import { gsap } from "gsap";

const HumanModelView = dynamic(() => import("../HumanModelView"), { ssr: false });

const TAGLINES = [
  "Digital twin initialized.",
  "Anatomical model loaded.",
  "Your profile. Your prediction.",
];

const PARALLAX_STRENGTH = 8;

/** Stable deps so the hero entrance effect runs once; array length must stay constant for React. */
const HERO_EFFECT_DEPS = Object.freeze([undefined]);

export default function HeroWithModel({ onAnimationsReady }) {
  const containerRef = useRef(null);
  const modelWrapRef = useRef(null);
  const headlineRef = useRef(null);
  const line1Ref = useRef(null);
  const line2Ref = useRef(null);
  const line3Ref = useRef(null);
  const [hoveredLine, setHoveredLine] = useState(null);
  const onAnimationsReadyRef = useRef(onAnimationsReady);
  onAnimationsReadyRef.current = onAnimationsReady;

  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 });

  const handleMouseMove = useCallback((e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setMouse({ x, y });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setMouse({ x: 0.5, y: 0.5 });
  }, []);

  useEffect(() => {
    if (!modelWrapRef.current) return;
    const rotX = (mouse.y - 0.5) * PARALLAX_STRENGTH;
    const rotY = (mouse.x - 0.5) * -PARALLAX_STRENGTH;
    gsap.to(modelWrapRef.current, {
      rotateX: rotX,
      rotateY: rotY,
      duration: 0.6,
      ease: "power2.out",
      overwrite: true,
    });
  }, [mouse.x, mouse.y]);

  useEffect(() => {
    if (!containerRef.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(modelWrapRef.current, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 1.4, ease: "power3.out" });
      if (headlineRef.current) {
        gsap.fromTo(headlineRef.current, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.9, delay: 0.3, ease: "power3.out" });
      }
      gsap.fromTo(line1Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 0.6, ease: "power3.out" });
      gsap.fromTo(line2Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 1, ease: "power3.out" });
      gsap.fromTo(line3Ref.current, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.8, delay: 1.4, ease: "power3.out" });
      gsap.delayedCall(1.6, () => onAnimationsReadyRef.current?.());
    }, containerRef);
    return () => ctx.revert();
  }, HERO_EFFECT_DEPS);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[50vh] lg:min-h-[calc(100vh-4rem)]"
      style={{ perspective: "1200px" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div ref={modelWrapRef} className="relative overflow-hidden w-full h-full min-h-[420px] transform-gpu" style={{ transformStyle: "preserve-3d" }}>
        <HumanModelView className="w-full h-full min-h-0" />
        <div className="absolute inset-0 pointer-events-none scan-line opacity-25" aria-hidden />
        <div className="absolute inset-0 cinematic-spotlight" aria-hidden />
      </div>

      <div className="absolute top-8 left-6 right-6 md:left-8 md:right-0 pointer-events-none">
        <h1 ref={headlineRef} className="hero-headline gradient-text max-w-lg" style={{ pointerEvents: "auto" }}>
          Your body. Decoded.
        </h1>
      </div>

      <div className="absolute bottom-6 left-6 space-y-1 font-mono text-xs text-[var(--color-primary)]/90 tracking-wide pointer-events-none">
        {TAGLINES.map((text, i) => {
          const ref = [line1Ref, line2Ref, line3Ref][i];
          const isHovered = hoveredLine === i;
          return (
            <p
              key={i}
              ref={ref}
              className={`cursor-default transition-all duration-200 ${i === 0 ? "text-[var(--color-primary)]" : i === 1 ? "text-[var(--color-primary)]/80" : "text-[var(--color-muted)] text-[11px]"} ${isHovered ? "text-glow opacity-100 scale-105" : ""}`}
              style={{ pointerEvents: "auto" }}
              onMouseEnter={() => setHoveredLine(i)}
              onMouseLeave={() => setHoveredLine(null)}
            >
              {text}
            </p>
          );
        })}
      </div>
    </div>
  );
}
