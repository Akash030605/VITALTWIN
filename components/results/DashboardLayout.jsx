"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useStore } from "../../store/useStore";
import { getLatestSubmission } from "../../lib/profileApi";
import ProfileSummary from "./ProfileSummary";
import MedicalConditionsSummary from "./MedicalConditionsSummary";

const EMPTY_STATE = (
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

export default function DashboardLayout({ children }) {
  const result = useStore((s) => s.result);
  const profile = useStore((s) => s.profile);
  const [mounted, setMounted] = useState(false);
  const [fetchedSubmission, setFetchedSubmission] = useState(null);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!result) return;
    getLatestSubmission()
      .then((res) => res?.ok && res?.data && setFetchedSubmission(res.data))
      .catch(() => {});
  }, [result]);

  if (!mounted || !result) {
    return EMPTY_STATE;
  }

  return (
    <>
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        <div className="rounded-xl glass-card px-6 py-4 w-full">
          <ProfileSummary profile={fetchedSubmission?.profile ?? profile} />
        </div>
        <div className="w-full min-w-0">
          <MedicalConditionsSummary conditions={fetchedSubmission?.input?.medical_conditions} />
        </div>
      </div>
      {children}
    </>
  );
}
