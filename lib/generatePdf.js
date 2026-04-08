/**
 * Doctor-ready PDF export for VitalTwin health reports.
 * Client-only — must be dynamically imported.
 */

const TEAL = [20, 184, 166];
const DARK = [8, 10, 13];
const LIGHT = [232, 236, 241];
const MUTED = [100, 116, 139];
const RED = [239, 68, 68];
const AMBER = [251, 191, 36];
const GREEN = [52, 211, 153];

function riskColor(level) {
  if (level === "RED") return RED;
  if (level === "YELLOW") return AMBER;
  return GREEN;
}

function riskLabel(level) {
  if (level === "RED") return "Critical";
  if (level === "YELLOW") return "At Risk";
  return "Healthy";
}

function priorityColor(priority) {
  if (priority === "CRITICAL") return RED;
  if (priority === "HIGH") return AMBER;
  return TEAL;
}

export async function generateReportPdf(profile, input, result) {
  const { jsPDF } = await import("jspdf");
  await import("jspdf-autotable");

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 16;
  const contentW = pageW - margin * 2;
  let y = margin;

  // ─── Header ───────────────────────────────────────────────────────────────
  doc.setFillColor(...DARK);
  doc.rect(0, 0, pageW, 28, "F");

  doc.setTextColor(...TEAL);
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("VitalTwin", margin, 12);

  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(...MUTED);
  doc.text("Healthcare Forensic Report", margin, 18);

  const date = new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" });
  doc.text(`Generated: ${date}`, pageW - margin, 12, { align: "right" });
  doc.text("For clinical reference only", pageW - margin, 18, { align: "right" });

  y = 36;

  // ─── Patient Info ──────────────────────────────────────────────────────────
  doc.setFillColor(15, 18, 22);
  doc.roundedRect(margin, y, contentW, 20, 2, 2, "F");
  doc.setTextColor(...TEAL);
  doc.setFontSize(7);
  doc.setFont("helvetica", "bold");
  doc.text("PATIENT", margin + 4, y + 5);

  const patientFields = [
    ["Name", profile?.name || "—"],
    ["Age", profile?.age || "—"],
    ["Gender", profile?.gender || "—"],
    ["Height", profile?.height ? `${profile.height} cm` : "—"],
    ["Weight", profile?.weight ? `${profile.weight} kg` : "—"],
    ["Activity", profile?.activity || "—"],
    ["Diet", profile?.diet || "—"],
  ];

  const colW = contentW / patientFields.length;
  patientFields.forEach(([label, value], i) => {
    const x = margin + i * colW + 4;
    doc.setTextColor(...MUTED);
    doc.setFontSize(6.5);
    doc.setFont("helvetica", "normal");
    doc.text(label, x, y + 10);
    doc.setTextColor(...LIGHT);
    doc.setFontSize(8);
    doc.setFont("helvetica", "bold");
    doc.text(String(value), x, y + 16);
  });

  y += 26;

  // ─── Vital Score + Biological Age ─────────────────────────────────────────
  const vitalScore = result?.vital_score?.current ?? result?.overall_health_score ?? "—";
  const bio = result?.biological_age;
  const bioAge = typeof bio === "object" ? bio?.biological_age : bio;
  const realAge = typeof bio === "object" ? bio?.real_age : profile?.age;
  const ageGap = typeof bio === "object" ? bio?.age_gap : null;
  const vitalMsg = result?.vital_score?.message || result?.vital_score?.interpretation || "";
  const bioMsg = typeof bio === "object" ? bio?.message || "" : "";

  // Two side-by-side metric boxes
  const boxH = 24;
  const halfW = (contentW - 4) / 2;

  // Vital Score box
  doc.setFillColor(15, 18, 22);
  doc.roundedRect(margin, y, halfW, boxH, 2, 2, "F");
  doc.setDrawColor(...TEAL);
  doc.setLineWidth(0.4);
  doc.roundedRect(margin, y, halfW, boxH, 2, 2, "S");
  doc.setTextColor(...MUTED);
  doc.setFontSize(6.5);
  doc.setFont("helvetica", "normal");
  doc.text("VITAL SCORE", margin + 4, y + 6);
  doc.setTextColor(...LIGHT);
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  doc.text(String(vitalScore), margin + 4, y + 18);
  doc.setTextColor(...MUTED);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text("/ 100", margin + 4 + doc.getTextWidth(String(vitalScore)) + 2, y + 18);

  // Bio Age box
  const box2X = margin + halfW + 4;
  doc.setFillColor(15, 18, 22);
  doc.roundedRect(box2X, y, halfW, boxH, 2, 2, "F");
  doc.setDrawColor(...TEAL);
  doc.roundedRect(box2X, y, halfW, boxH, 2, 2, "S");
  doc.setTextColor(...MUTED);
  doc.setFontSize(6.5);
  doc.setFont("helvetica", "normal");
  doc.text("BIOLOGICAL AGE", box2X + 4, y + 6);
  doc.setTextColor(...LIGHT);
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  doc.text(bioAge != null ? String(bioAge) : "—", box2X + 4, y + 18);
  doc.setTextColor(...MUTED);
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  if (realAge != null) {
    const gapTxt = ageGap != null ? ` (${ageGap > 0 ? "+" : ""}${ageGap}y gap)` : "";
    doc.text(`Chronological: ${realAge}${gapTxt}`, box2X + 4, y + 22);
  }

  y += boxH + 4;

  // Summary messages
  if (vitalMsg) {
    doc.setTextColor(...MUTED);
    doc.setFontSize(8);
    doc.setFont("helvetica", "italic");
    const wrapped = doc.splitTextToSize(vitalMsg, contentW);
    doc.text(wrapped, margin, y);
    y += wrapped.length * 4 + 2;
  }
  if (bioMsg) {
    doc.setTextColor(...MUTED);
    doc.setFontSize(8);
    const wrapped = doc.splitTextToSize(bioMsg, contentW);
    doc.text(wrapped, margin, y);
    y += wrapped.length * 4 + 2;
  }

  y += 4;

  // ─── Organ Health Table ────────────────────────────────────────────────────
  const organs = result?.organs ?? {};
  const organRows = Object.entries(organs).map(([name, data]) => [
    name.charAt(0).toUpperCase() + name.slice(1),
    data?.health_score != null ? `${data.health_score}%` : "—",
    riskLabel(data?.risk_level),
    data?.risk_level || "—",
    data?.summary?.slice(0, 80) || "—",
  ]);

  if (organRows.length > 0) {
    doc.setTextColor(...TEAL);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("ORGAN HEALTH", margin, y);
    y += 4;

    doc.autoTable({
      startY: y,
      margin: { left: margin, right: margin },
      head: [["Organ", "Score", "Status", "Risk", "Summary"]],
      body: organRows,
      theme: "plain",
      styles: { fontSize: 7.5, cellPadding: 2.5, textColor: LIGHT, fillColor: [15, 18, 22] },
      headStyles: { textColor: TEAL, fillColor: [10, 15, 20], fontStyle: "bold", fontSize: 7 },
      alternateRowStyles: { fillColor: [12, 15, 19] },
      columnStyles: {
        0: { fontStyle: "bold", cellWidth: 22 },
        1: { cellWidth: 16, halign: "center" },
        2: { cellWidth: 20 },
        3: { cellWidth: 14 },
        4: { cellWidth: "auto" },
      },
      didDrawCell: (data) => {
        if (data.column.index === 2 && data.section === "body") {
          const risk = organRows[data.row.index]?.[3];
          doc.setTextColor(...riskColor(risk));
        }
      },
    });
    y = doc.lastAutoTable.finalY + 6;
  }

  // ─── Body Stress ──────────────────────────────────────────────────────────
  const stress = result?.body_stress;
  if (stress) {
    doc.setTextColor(...TEAL);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("BODY STRESS", margin, y);
    y += 4;

    const stressRows = [];
    const zones = stress?.heatmap_zones ?? stress?.zones ?? {};
    const systems = stress?.systems ?? {};
    Object.entries({ ...systems, ...zones }).forEach(([key, val]) => {
      const level = typeof val === "object" ? val?.level ?? val?.intensity : val;
      stressRows.push([key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), String(level ?? "—")]);
    });

    if (stressRows.length > 0) {
      doc.autoTable({
        startY: y,
        margin: { left: margin, right: margin },
        head: [["Area / System", "Level"]],
        body: stressRows,
        theme: "plain",
        styles: { fontSize: 7.5, cellPadding: 2, textColor: LIGHT, fillColor: [15, 18, 22] },
        headStyles: { textColor: TEAL, fillColor: [10, 15, 20], fontStyle: "bold", fontSize: 7 },
        alternateRowStyles: { fillColor: [12, 15, 19] },
        columnStyles: { 0: { cellWidth: 70 }, 1: { cellWidth: "auto" } },
      });
      y = doc.lastAutoTable.finalY + 6;
    }
  }

  // ─── Future Self Trajectory ────────────────────────────────────────────────
  const timeline = result?.future_self?.timeline ?? [];
  if (timeline.length > 0) {
    if (y > pageH - 50) { doc.addPage(); y = margin; }
    doc.setTextColor(...TEAL);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("FUTURE SELF TRAJECTORY", margin, y);
    y += 4;

    const timelineRows = timeline.map((t) => [
      t.label ?? `${t.year}y`,
      t.vitality_score != null ? String(t.vitality_score) : "—",
      t.biological_age != null ? String(t.biological_age) : "—",
      (t.changes ?? []).slice(0, 2).join("; ") || "—",
    ]);

    doc.autoTable({
      startY: y,
      margin: { left: margin, right: margin },
      head: [["Period", "Vitality Score", "Bio Age", "Key Changes"]],
      body: timelineRows,
      theme: "plain",
      styles: { fontSize: 7.5, cellPadding: 2.5, textColor: LIGHT, fillColor: [15, 18, 22] },
      headStyles: { textColor: TEAL, fillColor: [10, 15, 20], fontStyle: "bold", fontSize: 7 },
      alternateRowStyles: { fillColor: [12, 15, 19] },
      columnStyles: { 0: { cellWidth: 20 }, 1: { cellWidth: 28, halign: "center" }, 2: { cellWidth: 20, halign: "center" }, 3: { cellWidth: "auto" } },
    });
    y = doc.lastAutoTable.finalY + 6;
  }

  // ─── Priority Recommendations ──────────────────────────────────────────────
  const recs = result?.priority_recommendations ?? [];
  if (recs.length > 0) {
    if (y > pageH - 50) { doc.addPage(); y = margin; }
    doc.setTextColor(...TEAL);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("PRIORITY RECOMMENDATIONS", margin, y);
    y += 4;

    const recRows = recs.map((r) => [r.priority ?? "—", r.action ?? "—", r.impact_summary ?? "—"]);

    doc.autoTable({
      startY: y,
      margin: { left: margin, right: margin },
      head: [["Priority", "Action", "Expected Impact"]],
      body: recRows,
      theme: "plain",
      styles: { fontSize: 7.5, cellPadding: 2.5, textColor: LIGHT, fillColor: [15, 18, 22] },
      headStyles: { textColor: TEAL, fillColor: [10, 15, 20], fontStyle: "bold", fontSize: 7 },
      alternateRowStyles: { fillColor: [12, 15, 19] },
      columnStyles: { 0: { cellWidth: 22 }, 1: { cellWidth: 70 }, 2: { cellWidth: "auto" } },
      didDrawCell: (data) => {
        if (data.column.index === 0 && data.section === "body") {
          const p = recRows[data.row.index]?.[0];
          doc.setTextColor(...priorityColor(p));
        }
      },
    });
    y = doc.lastAutoTable.finalY + 6;
  }

  // ─── Health Inputs + Medications ──────────────────────────────────────────
  if (y > pageH - 60) { doc.addPage(); y = margin; }
  doc.setTextColor(...TEAL);
  doc.setFontSize(9);
  doc.setFont("helvetica", "bold");
  doc.text("HEALTH INPUTS & MEDICATIONS", margin, y);
  y += 4;

  const conditions = Array.isArray(input?.medical_conditions) ? input.medical_conditions : [];
  const medications = Array.isArray(input?.medications) ? input.medications : [];

  const inputRows = [
    ["Smoking", input?.smoking || "—"],
    ["Alcohol", input?.alcohol || "—"],
    ["Sleep", input?.sleep ? `${input.sleep}h per night` : "—"],
    ["Stress Level", input?.stress || "—"],
    ["Medical Conditions", conditions.length > 0 ? conditions.join(", ") : "None reported"],
    ["Medications", medications.length > 0 ? medications.join(", ") : "None reported"],
  ];

  doc.autoTable({
    startY: y,
    margin: { left: margin, right: margin },
    body: inputRows,
    theme: "plain",
    styles: { fontSize: 7.5, cellPadding: 2.5, textColor: LIGHT, fillColor: [15, 18, 22] },
    alternateRowStyles: { fillColor: [12, 15, 19] },
    columnStyles: { 0: { fontStyle: "bold", cellWidth: 42, textColor: MUTED }, 1: { cellWidth: "auto" } },
  });
  y = doc.lastAutoTable.finalY + 6;

  // ─── Footer on all pages ──────────────────────────────────────────────────
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFillColor(...DARK);
    doc.rect(0, pageH - 10, pageW, 10, "F");
    doc.setTextColor(...MUTED);
    doc.setFontSize(6.5);
    doc.setFont("helvetica", "normal");
    doc.text("Generated by VitalTwin — not a substitute for professional medical advice. vitaltwin.health", margin, pageH - 4);
    doc.text(`Page ${i} of ${totalPages}`, pageW - margin, pageH - 4, { align: "right" });
  }

  const patientName = (profile?.name || "report").replace(/\s+/g, "-").toLowerCase();
  doc.save(`VitalTwin-${patientName}-${new Date().toISOString().slice(0, 10)}.pdf`);
}
