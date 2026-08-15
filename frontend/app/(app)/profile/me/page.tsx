"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { EducationForm } from "@/components/profile/EducationForm";
import { EducationList } from "@/components/profile/EducationList";
import { EmploymentForm } from "@/components/profile/EmploymentForm";
import { EmploymentList } from "@/components/profile/EmploymentList";
import { ProfileUpdateForm } from "@/components/profile/ProfileUpdateForm";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { useProfileData } from "@/hooks/useProfileData";
import type { Profile } from "@/types/profile";

export default function ProfileMePage() {
  const router = useRouter();
  const { profile, education, employment, isLoading, error, refetch } =
    useProfileData();
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  // Use updated profile from PATCH response if available, otherwise fall back to fetched
  const displayProfile = currentProfile ?? profile;

  async function handleDeleteAccount() {
    setDeleting(true);
    setDeleteError("");
    try {
      const res = await fetch("/api/profile/me", {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        router.push("/");
        return;
      }
      setDeleteError("Could not delete account. Please try again.");
    } catch {
      setDeleteError("Network error. Please try again.");
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Spinner size="h-8 w-8" />
      </div>
    );
  }

  if (error || !displayProfile) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-2xl">
          <ErrorBanner message={error ?? "Profile not found."} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-2xl space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            My Profile
          </h1>
          <span className="text-sm text-gray-500">{displayProfile.email}</span>
        </div>

        {/* Profile update form */}
        <ProfileUpdateForm
          profile={displayProfile}
          onUpdated={(updated) => setCurrentProfile(updated)}
        />

        {/* Education section */}
        <section
          aria-labelledby="edu-list-heading"
          className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-gray-200"
        >
          <h2
            id="edu-list-heading"
            className="mb-4 text-lg font-semibold text-gray-900"
          >
            Education
          </h2>
          <EducationList items={education} onChanged={refetch} />
        </section>

        <EducationForm onAdded={refetch} />

        {/* Employment section */}
        <section
          aria-labelledby="emp-list-heading"
          className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-gray-200"
        >
          <h2
            id="emp-list-heading"
            className="mb-4 text-lg font-semibold text-gray-900"
          >
            Employment
          </h2>
          <EmploymentList items={employment} onChanged={refetch} />
        </section>

        <EmploymentForm onAdded={refetch} />

        {/* Danger zone */}
        <section
          aria-labelledby="danger-heading"
          className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-red-200"
        >
          <h2
            id="danger-heading"
            className="mb-2 text-lg font-semibold text-red-600"
          >
            Danger zone
          </h2>
          <p className="mb-4 text-sm text-gray-600">
            Permanently delete your account and all associated data. This cannot
            be undone.
          </p>

          {deleteError && (
            <div className="mb-4">
              <ErrorBanner message={deleteError} />
            </div>
          )}

          {showDeleteConfirm ? (
            <div className="flex items-center gap-3">
              <p className="text-sm font-medium text-gray-700">Are you sure?</p>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-60"
              >
                {deleting && <Spinner size="h-3.5 w-3.5" color="text-white" />}
                Yes, delete my account
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-100 focus:outline-none"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(true)}
              className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              Delete account
            </button>
          )}
        </section>
      </div>
    </div>
  );
}
