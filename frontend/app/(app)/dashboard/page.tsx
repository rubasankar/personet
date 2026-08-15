"use client";

import Link from "next/link";
import { ProfileCard } from "@/components/dashboard/ProfileCard";
import { SuggestionCard } from "@/components/dashboard/SuggestionCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import { Spinner } from "@/components/ui/Spinner";
import { useDashboardData } from "@/hooks/useDashboardData";

export default function DashboardPage() {
  const {
    profile,
    profileError,
    suggestions,
    suggestionsLoading,
    suggestionsError,
  } = useDashboardData();

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-3xl space-y-8">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Dashboard
        </h1>

        {/* Profile section */}
        <section aria-label="Your profile">
          {profileError ? (
            <ErrorBanner message={profileError} />
          ) : profile ? (
            <ProfileCard profile={profile} />
          ) : (
            <div
              className="animate-pulse rounded-2xl bg-white px-8 py-10 shadow-sm ring-1 ring-gray-200"
              aria-busy="true"
            >
              <div className="mb-3 h-5 w-1/3 rounded bg-gray-200" />
              <div className="mb-2 h-3 w-2/3 rounded bg-gray-200" />
              <div className="h-3 w-1/4 rounded bg-gray-200" />
            </div>
          )}
        </section>

        {/* Suggestions section */}
        <section aria-label="Connection suggestions">
          <div className="mb-4 flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">
              People you may know
            </h2>
            {suggestionsLoading && <Spinner />}
          </div>

          {suggestionsError ? (
            <ErrorBanner message={suggestionsError} />
          ) : suggestionsLoading ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : suggestions.length === 0 ? (
            <div className="rounded-xl bg-white px-6 py-10 text-center shadow-sm ring-1 ring-gray-200">
              <p className="text-sm text-gray-500">
                No suggestions yet - add your education or employment to get
                started.
              </p>
              <Link
                href="/profile/me"
                className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500 hover:underline"
              >
                Update your profile
              </Link>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {suggestions.map((s) => (
                <SuggestionCard key={s.id} suggestion={s} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
