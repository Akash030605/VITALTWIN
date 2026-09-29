"use client";

import { useRef, useState } from "react";
import { parseAppleHealthXML, parseGoogleFitJSON, normalizeImportedData } from "../../lib/parseHealthData";

export default function HealthDataImport({ onImport }) {
  const fileRef = useRef(null);
  const [status, setStatus] = useState(null); // null | { type: "success"|"error", message, fields? }
  const [dragging, setDragging] = useState(false);

  const processFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result;
      if (!content) return setStatus({ type: "error", message: "Could not read file." });

      let raw = {};
      if (file.name.endsWith(".xml")) {
        raw = parseAppleHealthXML(content);
      } else if (file.name.endsWith(".json")) {
        raw = parseGoogleFitJSON(content);
      } else {
        return setStatus({ type: "error", message: "Unsupported file type. Use Apple Health export.xml or Google Fit .json." });
      }

      const { profileFields, inputFields, meta } = normalizeImportedData(raw);
      const total = Object.keys(profileFields).length + Object.keys(inputFields).length;

      if (total === 0) {
        return setStatus({ type: "error", message: "No recognizable health data found. Try the standard export from the Health app." });
      }

      onImport(profileFields, inputFields);

      const imported = [
        profileFields.height && `Height: ${profileFields.height} cm`,
        profileFields.weight && `Weight: ${profileFields.weight} kg`,
        inputFields.sleep && `Sleep: ${inputFields.sleep}h avg`,
        meta?.steps && `Steps: ${meta.steps.toLocaleString()}/day`,
        meta?.heartRate && `Heart rate: ${meta.heartRate} bpm`,
      ].filter(Boolean);

      setStatus({ type: "success", message: `Imported: ${imported.join(" · ")}` });
    };
    reader.onerror = () => setStatus({ type: "error", message: "File read error. Please try again." });
    if (file.name.endsWith(".xml")) {
      reader.readAsText(file);
    } else {
      reader.readAsText(file);
    }
  };

  const handleFile = (e) => {
    processFile(e.target.files?.[0]);
    e.target.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    processFile(e.dataTransfer.files?.[0]);
  };

  return (
    <div className="mt-4 pt-4 border-t border-slate-200">
      <p className="text-xs font-medium text-(--color-muted) uppercase tracking-wider mb-2">
        Or import from wearable
      </p>
      <div
        className={`relative rounded-xl border-2 border-dashed px-4 py-5 text-center cursor-pointer transition-all duration-200 ${
          dragging
            ? "border-(--color-primary) bg-(--color-primary)/10"
            : "border-slate-300 bg-slate-50 hover:border-(--color-primary)/50 hover:bg-emerald-50"
        }`}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && fileRef.current?.click()}
        aria-label="Import health data file"
      >
        <input
          ref={fileRef}
          type="file"
          accept=".xml,.json"
          onChange={handleFile}
          className="hidden"
          aria-hidden
        />
        <div className="flex flex-col items-center gap-1.5">
          <svg className="w-7 h-7 text-(--color-primary)/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 8.25H7.5a2.25 2.25 0 00-2.25 2.25v9a2.25 2.25 0 002.25 2.25h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25H15M9 12l3 3m0 0l3-3m-3 3V2.25" />
          </svg>
          <p className="text-sm text-(--color-muted)">
            Drop <span className="text-(--foreground)">Apple Health</span> export.xml or{" "}
            <span className="text-(--foreground)">Google Fit</span> .json
          </p>
          <p className="text-xs text-(--color-muted)/60">Auto-fills height, weight &amp; sleep</p>
        </div>
      </div>

      {status && (
        <div
          className={`mt-2 rounded-lg px-3 py-2 text-xs ${
            status.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-700"
              : "bg-red-50 border border-red-200 text-red-600"
          }`}
          role="status"
        >
          {status.message}
        </div>
      )}
    </div>
  );
}
