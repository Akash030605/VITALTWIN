"use client";

import { useRef, useEffect } from "react";

const FIELDS = ["name", "age", "gender", "height", "weight", "diet", "activity"];
const LABELS = {
  name: "Name",
  age: "Age",
  gender: "Gender",
  height: "Height (cm)",
  weight: "Weight (kg)",
  diet: "Diet",
  activity: "Activity level",
};

export default function ProfilePopup({ profile, open, onClose, anchorRef }) {
  const popupRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e) => {
      if (
        popupRef.current &&
        !popupRef.current.contains(e.target) &&
        anchorRef?.current &&
        !anchorRef.current.contains(e.target)
      ) {
        onClose();
      }
    };
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open, onClose, anchorRef]);

  const entries = FIELDS.filter((k) => profile?.[k] != null && String(profile[k]).trim() !== "");

  if (!open) return null;

  return (
    <div
      ref={popupRef}
      className="absolute right-0 top-full z-50 mt-2 w-72 rounded-xl border border-slate-200 bg-white py-3 shadow-xl shadow-slate-900/8"
      role="dialog"
      aria-label="Profile details"
    >
      <div className="border-b border-slate-100 px-4 pb-2 mb-2">
        <p className="font-mono text-xs font-medium text-(--color-primary) uppercase tracking-wider">Profile</p>
      </div>
      <div className="px-4 space-y-2 max-h-64 overflow-y-auto">
        {entries.length === 0 ? (
          <p className="text-sm text-(--color-muted)">No profile data yet.</p>
        ) : (
          entries.map((key) => (
            <div key={key} className="flex justify-between gap-3 text-sm">
              <span className="text-(--color-muted) shrink-0">{LABELS[key]}</span>
              <span className="text-(--foreground) text-right break-words">{profile[key]}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
