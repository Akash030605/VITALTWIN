"use client";

import { useState, useRef } from "react";

export default function MedicationsField({ medications, onChange }) {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef(null);

  const add = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    if (medications.includes(trimmed)) {
      setInputValue("");
      return;
    }
    onChange([...medications, trimmed]);
    setInputValue("");
    inputRef.current?.focus();
  };

  const remove = (med) => onChange(medications.filter((m) => m !== med));

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      add();
    }
    if (e.key === "Backspace" && !inputValue && medications.length > 0) {
      remove(medications[medications.length - 1]);
    }
  };

  return (
    <div data-field className="space-y-2 pt-2 border-t border-slate-200">
      <label className="block text-sm font-medium text-(--foreground)">
        Medications &amp; prescriptions
      </label>
      <p className="text-xs text-(--color-muted) mb-1">
        Type a medication name and press Enter or click Add. Optional.
      </p>
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          placeholder="e.g. Metformin 500mg, Lisinopril 10mg…"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-foreground placeholder:text-(--color-muted-dim) focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15"
          aria-label="Add medication"
        />
        <button
          type="button"
          onClick={add}
          className="shrink-0 rounded-lg border border-(--color-primary)/40 bg-(--color-primary)/10 px-4 py-2 text-sm font-medium text-(--color-primary) transition-all hover:bg-(--color-primary)/20 hover:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/40"
        >
          Add
        </button>
      </div>
      {medications.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {medications.map((med) => (
            <span
              key={med}
              className="inline-flex items-center gap-1.5 rounded-lg bg-(--color-primary)/10 border border-(--color-primary)/25 pl-3 pr-1 py-1.5 text-sm text-(--foreground)"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-(--color-primary) shrink-0" aria-hidden />
              {med}
              <button
                type="button"
                onClick={() => remove(med)}
                className="p-1 rounded text-(--color-muted) hover:text-(--foreground) focus:outline-none"
                aria-label={`Remove ${med}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
