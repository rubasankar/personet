"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Suggestion } from "@/types/network";
import type { Profile } from "@/types/profile";

interface DashboardData {
  profile: Profile | null;
  profileError: string | null;
  suggestions: Suggestion[];
  suggestionsLoading: boolean;
  suggestionsError: string | null;
}

export function useDashboardData(): DashboardData {
  const router = useRouter();

  const [profile, setProfile] = useState<Profile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchProfile() {
      try {
        const res = await fetch("/api/profile/me", { credentials: "include" });
        if (res.status === 401 || res.status === 403) {
          router.push("/login");
          return;
        }
        if (!res.ok) {
          if (!cancelled)
            setProfileError("Could not load your profile. Please refresh.");
          return;
        }
        const data: Profile = await res.json();
        if (!cancelled) setProfile(data);
      } catch {
        if (!cancelled)
          setProfileError(
            "Unable to reach the server. Please check your connection.",
          );
      }
    }

    async function fetchSuggestions() {
      try {
        const res = await fetch("/api/network/suggestions", {
          credentials: "include",
        });
        if (res.status === 503) {
          if (!cancelled)
            setSuggestionsError(
              "The suggestions service is temporarily unavailable. Please try again later.",
            );
          return;
        }
        if (!res.ok) {
          if (!cancelled)
            setSuggestionsError(
              "Could not load suggestions. Please refresh the page.",
            );
          return;
        }
        const data: Suggestion[] = await res.json();
        if (!cancelled) setSuggestions(data);
      } catch {
        if (!cancelled)
          setSuggestionsError(
            "Unable to load suggestions. Please check your connection.",
          );
      } finally {
        if (!cancelled) setSuggestionsLoading(false);
      }
    }

    Promise.allSettled([fetchProfile(), fetchSuggestions()]);

    return () => {
      cancelled = true;
    };
  }, [router]);

  return {
    profile,
    profileError,
    suggestions,
    suggestionsLoading,
    suggestionsError,
  };
}
