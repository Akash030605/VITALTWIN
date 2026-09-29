"use client";

import { useMemo } from "react";
import OrganSection from "./OrganSection";

const RISK_ORDER = { RED: 0, YELLOW: 1, GREEN: 2 };
const ORGAN_IDS = ["heart", "brain", "liver", "kidney", "lungs"];

function sortOrgansByRisk(organs) {
  if (!organs) return ORGAN_IDS;
  return [...ORGAN_IDS].sort((a, b) => {
    const ra = RISK_ORDER[organs[a]?.risk_level] ?? 2;
    const rb = RISK_ORDER[organs[b]?.risk_level] ?? 2;
    return ra - rb;
  });
}

export default function ReportOrgansSection({ result }) {
  const organs = result?.organs;
  const organOrder = useMemo(() => sortOrgansByRisk(organs), [organs]);

  if (!organs || Object.keys(organs).length === 0) return null;

  return (
    <section className="mb-8" id="organs" aria-labelledby="organs-heading">
      <h2 id="organs-heading" className="text-xs font-medium text-(--color-primary) uppercase tracking-wider mb-2">Organs</h2>
      <p className="text-sm text-(--color-muted) mb-6">Organ health and risk. Shown by risk level (highest first).</p>
      <div className="space-y-6">
        {organOrder.map((organId) => (
          <OrganSection key={organId} organId={organId} organData={organs[organId]} />
        ))}
      </div>
    </section>
  );
}
