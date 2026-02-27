"use client";

export default function DashboardBackground() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none" aria-hidden>
      <div className="absolute inset-0 bg-dot-grid opacity-80" />
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(180deg, rgba(20, 184, 166, 0.04) 0%, transparent 40%, transparent 60%, rgba(20, 184, 166, 0.03) 100%)",
        }}
      />
      <div className="pulse-wave-bg" />
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(20, 184, 166, 0.06) 0%, transparent 50%)",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 100% 100% at 50% 50%, transparent 40%, rgba(0,0,0,0.35) 100%)",
        }}
      />
    </div>
  );
}
