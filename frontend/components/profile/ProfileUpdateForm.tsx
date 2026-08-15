"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type { Profile, ProfileUpdateFieldErrors } from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

interface ProfileUpdateFormProps {
  profile: Profile;
  onUpdated: (updated: Profile) => void;
}

export function ProfileUpdateForm({
  profile,
  onUpdated,
}: ProfileUpdateFormProps) {
  const [name, setName] = useState(profile.name);
  const [bio, setBio] = useState(profile.bio ?? "");
  const [location, setLocation] = useState(profile.location ?? "");

  const [fieldErrors, setFieldErrors] = useState<ProfileUpdateFieldErrors>({});
  const [serviceError, setServiceError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    setServiceError("");
    setSuccess(false);
    setIsLoading(true);

    try {
      // Only send fields that have values; omit empty strings so PATCH leaves them unchanged
      const body: Record<string, string> = {};
      if (name.trim()) body.name = name.trim();
      if (bio.trim()) body.bio = bio.trim();
      if (location.trim()) body.location = location.trim();

      const res = await fetch("/api/profile/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const updated: Profile = await res.json();
        setSuccess(true);
        onUpdated(updated);
        return;
      }

      if (res.status === 422) {
        const data = await res.json();
        const detail: FastAPIValidationError[] = data.detail ?? [];
        setFieldErrors(
          parseValidationErrors(detail) as ProfileUpdateFieldErrors,
        );
        return;
      }

      if (res.status === 503) {
        setServiceError(
          "The service is temporarily unavailable. Please try again later.",
        );
        return;
      }

      setServiceError("An unexpected error occurred. Please try again.");
    } catch {
      setServiceError(
        "Unable to reach the server. Please check your connection.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section
      aria-labelledby="profile-update-heading"
      className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-gray-200"
    >
      <h2
        id="profile-update-heading"
        className="mb-6 text-lg font-semibold text-gray-900"
      >
        Profile details
      </h2>

      {success && (
        <div className="mb-5">
          <SuccessBanner message="Profile updated successfully." />
        </div>
      )}
      {serviceError && (
        <div className="mb-5">
          <ErrorBanner message={serviceError} />
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <div>
          <label
            htmlFor="profile-name"
            className="block text-sm font-medium text-gray-700"
          >
            Name
          </label>
          <input
            id="profile-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.name ? "profile-name-error" : undefined
            }
            aria-invalid={!!fieldErrors.name}
            className={fieldClass(!!fieldErrors.name)}
          />
          <FieldError id="profile-name-error" message={fieldErrors.name} />
        </div>

        <div>
          <label
            htmlFor="profile-bio"
            className="block text-sm font-medium text-gray-700"
          >
            Bio <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            id="profile-bio"
            rows={3}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            disabled={isLoading}
            aria-describedby={fieldErrors.bio ? "profile-bio-error" : undefined}
            aria-invalid={!!fieldErrors.bio}
            className={`${fieldClass(!!fieldErrors.bio)} resize-none`}
            placeholder="e.g. Senior engineer · open to opportunities"
            maxLength={500}
          />
          <FieldError id="profile-bio-error" message={fieldErrors.bio} />
        </div>

        <div>
          <label
            htmlFor="profile-location"
            className="block text-sm font-medium text-gray-700"
          >
            Location <span className="text-gray-400">(optional)</span>
          </label>
          <input
            id="profile-location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.location ? "profile-location-error" : undefined
            }
            aria-invalid={!!fieldErrors.location}
            className={fieldClass(!!fieldErrors.location)}
            placeholder="e.g. London, UK"
          />
          <FieldError
            id="profile-location-error"
            message={fieldErrors.location}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading && <Spinner size="h-4 w-4" color="text-white" />}
          {isLoading ? "Saving..." : "Save changes"}
        </button>
      </form>
    </section>
  );
}
