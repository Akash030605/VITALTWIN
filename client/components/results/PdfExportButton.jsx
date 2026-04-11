"use client";

import { useState } from "react";
import { useStore } from "../../store/useStore";

export default function PdfExportButton() {
  const profile = useStore((s) => s.profile);
  const input = useStore((s) => s.input);
  const result = useStore((s) => s.result);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error

  const handleExport = async () => {
    if (status === "loading") return;
    setStatus("loading");
    try {
      const { generateReportPdf } = await import("../../lib/generatePdf");
      await generateReportPdf(profile, input, result);
      setStatus("done");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (err) {
      console.error("PDF export error:", err);
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  const label = {
    idle: "Export PDF",
    loading: "Generating…",
    done: "Downloaded!",
    error: "Export failed",
  }[status];

  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={status === "loading"}
      className="inline-flex items-center gap-1.5 text-sm text-(--color-primary) font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-(--color-primary)/50 rounded py-1.5 px-2 transition-opacity hover:opacity-90 disabled:opacity-50 disabled:pointer-events-none"
      aria-label="Export health report as PDF"
    >
      {status === "loading" ? (
        <svg className="w-3.5 h-3.5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24" aria-hidden>
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
      )}
      {label}
    </button>
  );
}
