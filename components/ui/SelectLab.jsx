"use client";

import { useState, useRef, useEffect } from "react";

export default function SelectLab({ id, value, onChange, options, placeholder, className = "" }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const displayOptions = options.filter(Boolean);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const handleSelect = (opt) => {
    onChange(opt);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        id={id}
        onClick={() => setOpen((o) => !o)}
        className="select-lab w-full rounded px-4 py-3 text-left text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 focus:ring-offset-0"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-labelledby={id ? `${id}-label` : undefined}
      >
        <span className={!value ? "text-[var(--color-muted)]" : ""}>
          {value || placeholder}
        </span>
        <span className={`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 transition-transform ${open ? "rotate-180" : ""}`} aria-hidden>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="var(--color-primary)" strokeWidth={2} className="h-5 w-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {open && (
        <div
          role="listbox"
          aria-label={placeholder}
          className="select-lab-dropdown absolute z-[100] mt-1.5 w-full max-h-[220px] overflow-hidden rounded-lg border-2 border-[var(--color-primary)] shadow-[0_8px_32px_rgba(0,0,0,0.8)]"
        >
          <ul className="max-h-[212px] overflow-y-auto py-1.5">
            {displayOptions.map((opt) => (
              <li
                key={opt}
                role="option"
                aria-selected={value === opt}
                onClick={() => handleSelect(opt)}
                className={`cursor-pointer px-4 py-2.5 text-sm transition-colors border-b border-[#1e3640] last:border-b-0 ${
                  value === opt
                    ? "bg-[#0f2e2b] text-[var(--color-scan)] font-medium"
                    : "bg-[#252d38] text-[#f1f5f9] hover:bg-[#1a3532] hover:text-[var(--color-scan)]"
                }`}
              >
                {opt}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
