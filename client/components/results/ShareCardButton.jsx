"use client";

import { useState, useRef } from "react";
import { useStore } from "../../store/useStore";
import ShareableCard from "./ShareableCard";

async function captureCard(ref) {
  const { default: html2canvas } = await import("html2canvas");
  const canvas = await html2canvas(ref.current, {
    backgroundColor: "#080a0d",
    scale: 2,
    useCORS: true,
    logging: false,
  });
  return canvas.toDataURL("image/png");
}

function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  a.click();
}

async function shareDataUrl(dataUrl, filename) {
  if (!navigator.share) return false;
  try {
    const res = await fetch(dataUrl);
    const blob = await res.blob();
    const file = new File([blob], filename, { type: "image/png" });
    await navigator.share({ files: [file], title: "VitalTwin Health Report" });
    return true;
  } catch {
    return false;
  }
}

export default function ShareCardButton() {
  const profile = useStore((s) => s.profile);
  const result = useStore((s) => s.result);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | capturing | ready | error
  const [dataUrl, setDataUrl] = useState(null);
  const cardRef = useRef(null);

  const filename = `VitalTwin-${(profile?.name || "report").replace(/\s+/g, "-").toLowerCase()}.png`;

  const handleOpen = () => setOpen(true);
  const handleClose = () => { setOpen(false); setStatus("idle"); setDataUrl(null); };

  const handleCapture = async () => {
    setStatus("capturing");
    try {
      const url = await captureCard(cardRef);
      setDataUrl(url);
      setStatus("ready");
    } catch (err) {
      console.error("Card capture error:", err);
      setStatus("error");
    }
  };

  const handleDownload = () => {
    if (dataUrl) downloadDataUrl(dataUrl, filename);
  };

  const handleShare = async () => {
    if (!dataUrl) return;
    const shared = await shareDataUrl(dataUrl, filename);
    if (!shared) downloadDataUrl(dataUrl, filename);
  };

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className="inline-flex items-center gap-1.5 text-sm text-(--color-primary) font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-(--color-primary)/50 rounded py-1.5 px-2 transition-opacity hover:opacity-90"
        aria-label="Share health report card"
      >
        <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
        </svg>
        Share card
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={handleClose}>
          <div className="relative bg-white rounded-2xl border border-slate-200 shadow-2xl shadow-slate-200/60 max-w-lg w-full p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-semibold text-foreground">Share your health card</p>
              <button type="button" onClick={handleClose} className="w-7 h-7 rounded-lg flex items-center justify-center text-(--color-muted) hover:text-foreground hover:bg-slate-100 transition-colors" aria-label="Close">×</button>
            </div>

            {/* Card preview (always rendered for capture) */}
            <div className="flex justify-center mb-4 overflow-hidden rounded-xl">
              <ShareableCard ref={cardRef} profile={profile} result={result} />
            </div>

            {status === "ready" && dataUrl && (
              <div className="flex justify-center mb-4 overflow-hidden rounded-xl border border-(--color-primary)/20">
                <img src={dataUrl} alt="Report card preview" className="w-full rounded-xl" />
              </div>
            )}

            {status === "error" && (
              <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-600" role="alert">
                Capture failed. Try scrolling back to the top and retrying.
              </div>
            )}

            <div className="flex gap-2 justify-end flex-wrap">
              {status === "idle" && (
                <button type="button" onClick={handleCapture} className="px-4 py-2 rounded-lg border border-(--color-primary)/50 bg-(--color-primary)/10 text-sm font-medium text-(--color-primary) hover:bg-(--color-primary)/20 transition-all">
                  Generate image
                </button>
              )}
              {status === "capturing" && (
                <button type="button" disabled className="px-4 py-2 rounded-lg border border-(--color-primary)/30 bg-(--color-primary)/5 text-sm font-medium text-(--color-primary) opacity-60 cursor-not-allowed flex items-center gap-2">
                  <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                  Capturing…
                </button>
              )}
              {status === "ready" && (
                <>
                  <button type="button" onClick={handleCapture} className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-(--color-muted) hover:text-foreground hover:bg-slate-50 transition-all">
                    Re-capture
                  </button>
                  <button type="button" onClick={handleDownload} className="px-4 py-2 rounded-lg border border-(--color-primary)/50 bg-(--color-primary)/10 text-sm font-medium text-(--color-primary) hover:bg-(--color-primary)/20 transition-all">
                    Download PNG
                  </button>
                  {typeof navigator !== "undefined" && navigator.share && (
                    <button type="button" onClick={handleShare} className="px-4 py-2 rounded-lg bg-(--color-primary) text-sm font-medium text-[#080a0d] hover:opacity-90 transition-all">
                      Share
                    </button>
                  )}
                </>
              )}
              {status === "error" && (
                <button type="button" onClick={handleCapture} className="px-4 py-2 rounded-lg border border-(--color-primary)/50 bg-(--color-primary)/10 text-sm font-medium text-(--color-primary) hover:bg-(--color-primary)/20 transition-all">
                  Retry
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
