"use client";

import Link from "next/link";
import { useStore } from "../../store/useStore";
import ProfileSummary from "./ProfileSummary";
import MedicalConditionsSummary from "./MedicalConditionsSummary";

export default function DashboardLayout({ children }) {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);

  if (!result) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4">
        <p className="text-[var(--color-muted)] text-center mb-6">Complete the health assessment to see your dashboard.</p>
        <Link
          href="/health-questions"
          className="text-[var(--color-primary)] font-medium hover:underline"
          aria-label="Start health assessment"
        >
          Start assessment
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6 rounded-xl glass-card px-6 py-4 inline-block">
        <ProfileSummary profile={profile} />
      </div>
      <MedicalConditionsSummary />
      {children}
    </>
  );
}
