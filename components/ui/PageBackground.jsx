"use client";

export default function PageBackground() {
  return (
    <div className="fixed inset-0 -z-10 bg-dot-grid" aria-hidden>
      {/* Atmospheric gradient */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(180deg, rgba(20, 184, 166, 0.06) 0%, transparent 45%, transparent 55%, rgba(0,0,0,0.12) 100%)",
        }}
      />
      {/* Cinematic vignette (stronger for game look) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 100% 100% at 50% 50%, transparent 35%, rgba(0,0,0,0.4) 80%, rgba(0,0,0,0.65) 100%)",
        }}
        aria-hidden
      />
      {/* Subtle film grain */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03] mix-blend-overlay"
        style={{
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          backgroundSize: "200px 200px",
        }}
        aria-hidden
      />
    </div>
  );
}
