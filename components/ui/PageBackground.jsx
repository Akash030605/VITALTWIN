"use client";

export default function PageBackground() {
  return (
    <div className="fixed inset-0 -z-10 bg-dot-grid" aria-hidden>
      {/* Atmospheric gradient */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(180deg, rgba(20, 184, 166, 0.06) 0%, transparent 45%, transparent 55%, rgba(0,0,0,0.08) 100%)",
        }}
      />
      {/* Cinematic vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 100% 100% at 50% 50%, transparent 40%, rgba(0,0,0,0.35) 85%, rgba(0,0,0,0.55) 100%)",
        }}
        aria-hidden
      />
    </div>
  );
}
