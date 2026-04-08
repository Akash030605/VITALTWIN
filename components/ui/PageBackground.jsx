"use client";

export default function PageBackground() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none" aria-hidden>
      <div className="absolute inset-0 bg-dot-grid opacity-50" />
      <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(5,150,105,0.04) 0%, transparent 30%)" }} />
    </div>
  );
}
