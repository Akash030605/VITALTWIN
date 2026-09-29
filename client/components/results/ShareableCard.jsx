"use client";

import { forwardRef } from "react";

/**
 * The off-screen card that html2canvas captures.
 * All colors MUST be hardcoded hex — html2canvas doesn't resolve CSS custom properties.
 */
const ShareableCard = forwardRef(function ShareableCard({ profile, result }, ref) {
  const vitalScore = result?.vital_score?.current ?? result?.overall_health_score ?? "—";
  const bio = result?.biological_age;
  const bioAge = typeof bio === "object" ? bio?.biological_age : bio;
  const realAge = typeof bio === "object" ? bio?.real_age : profile?.age;
  const ageGap = typeof bio === "object" ? bio?.age_gap : null;
  const category = result?.vital_score?.category ?? "";

  const organs = result?.organs ?? {};
  const topRisks = Object.entries(organs)
    .filter(([, d]) => d?.risk_level === "RED" || d?.risk_level === "YELLOW")
    .sort((a, b) => (a[1].risk_level === "RED" ? -1 : 1))
    .slice(0, 3);

  const gapColor = ageGap == null ? "#64748b" : ageGap > 5 ? "#ef4444" : ageGap > 0 ? "#fbbf24" : "#34d399";
  const scoreColor = vitalScore >= 75 ? "#34d399" : vitalScore >= 55 ? "#14b8a6" : vitalScore >= 40 ? "#fbbf24" : "#ef4444";

  const date = new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });

  return (
    <div
      ref={ref}
      style={{
        width: "520px",
        height: "290px",
        background: "#080a0d",
        borderRadius: "16px",
        border: "1px solid rgba(20,184,166,0.25)",
        fontFamily: "system-ui, -apple-system, sans-serif",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Dot grid background */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: "radial-gradient(circle at 1px 1px, rgba(20,184,166,0.1) 1px, transparent 0)",
        backgroundSize: "20px 20px",
        pointerEvents: "none",
      }} />

      {/* Top teal gradient band */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "3px", background: "linear-gradient(90deg,#14b8a6,#2dd4bf,transparent)" }} />

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px 10px", position: "relative" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(20,184,166,0.15)", border: "1px solid rgba(20,184,166,0.4)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#14b8a6", fontWeight: 700, fontSize: "11px" }}>VT</span>
          </div>
          <div>
            <div style={{ color: "#e8ecf1", fontWeight: 700, fontSize: "14px", letterSpacing: "-0.3px" }}>VitalTwin</div>
            <div style={{ color: "#64748b", fontSize: "10px" }}>Health Forensic Report</div>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          {profile?.name && <div style={{ color: "#e8ecf1", fontWeight: 600, fontSize: "13px" }}>{profile.name}</div>}
          <div style={{ color: "#64748b", fontSize: "10px" }}>{date}</div>
        </div>
      </div>

      {/* Main metrics row */}
      <div style={{ display: "flex", gap: "10px", padding: "0 20px", flex: 1 }}>
        {/* Vital Score */}
        <div style={{ background: "rgba(15,18,22,0.8)", border: "1px solid rgba(20,184,166,0.2)", borderRadius: "12px", padding: "14px 16px", flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div style={{ color: "#64748b", fontSize: "9px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>Vital Score</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "4px" }}>
            <span style={{ color: scoreColor, fontSize: "42px", fontWeight: 700, lineHeight: 1 }}>{vitalScore}</span>
            <span style={{ color: "#475569", fontSize: "16px", fontWeight: 400, marginBottom: "5px" }}>/100</span>
          </div>
          {category && <div style={{ color: scoreColor, fontSize: "10px", fontWeight: 600, opacity: 0.9 }}>{category}</div>}
        </div>

        {/* Biological Age */}
        <div style={{ background: "rgba(15,18,22,0.8)", border: "1px solid rgba(20,184,166,0.2)", borderRadius: "12px", padding: "14px 16px", flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div style={{ color: "#64748b", fontSize: "9px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>Biological Age</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "4px" }}>
            <span style={{ color: "#e8ecf1", fontSize: "42px", fontWeight: 700, lineHeight: 1 }}>{bioAge ?? "—"}</span>
            {realAge && <span style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>vs {realAge}</span>}
          </div>
          {ageGap != null && (
            <div style={{ color: gapColor, fontSize: "10px", fontWeight: 600 }}>
              {ageGap > 0 ? `+${ageGap}` : ageGap} year{Math.abs(ageGap) !== 1 ? "s" : ""} {ageGap > 0 ? "older" : "younger"}
            </div>
          )}
        </div>

        {/* Organ risks */}
        {topRisks.length > 0 && (
          <div style={{ background: "rgba(15,18,22,0.8)", border: "1px solid rgba(20,184,166,0.2)", borderRadius: "12px", padding: "14px 16px", flex: 1, display: "flex", flexDirection: "column", gap: "8px" }}>
            <div style={{ color: "#64748b", fontSize: "9px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>Organ Risks</div>
            {topRisks.map(([name, data]) => {
              const isRed = data.risk_level === "RED";
              const c = isRed ? "#ef4444" : "#fbbf24";
              const bg = isRed ? "rgba(127,29,29,0.4)" : "rgba(120,53,15,0.4)";
              return (
                <div key={name} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: bg, borderRadius: "6px", padding: "4px 8px" }}>
                  <span style={{ color: "#e8ecf1", fontSize: "11px", fontWeight: 600, textTransform: "capitalize" }}>{name}</span>
                  <span style={{ color: c, fontSize: "10px", fontWeight: 700 }}>{isRed ? "CRITICAL" : "AT RISK"}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 20px 14px", position: "relative" }}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#14b8a6" }} />
          <span style={{ color: "#64748b", fontSize: "10px" }}>vitaltwin.health</span>
        </div>
        <span style={{ color: "#475569", fontSize: "9px" }}>Powered by AI · Not medical advice</span>
      </div>
    </div>
  );
});

export default ShareableCard;
