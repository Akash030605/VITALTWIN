import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-[var(--color-bg)] text-[var(--foreground)]">
      <h1 className="text-2xl font-semibold mb-2">Page not found</h1>
      <p className="text-[var(--color-muted)] mb-6 text-center">
        The page you’re looking for doesn’t exist or the URL may have changed.
      </p>
      <Link
        href="/"
        className="rounded-lg border border-[var(--color-primary)]/60 bg-[var(--color-primary)]/10 px-6 py-3 text-sm font-medium text-[var(--color-primary)] hover:bg-[var(--color-primary)]/20 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50"
      >
        Back to VitalTwin
      </Link>
    </div>
  );
}
