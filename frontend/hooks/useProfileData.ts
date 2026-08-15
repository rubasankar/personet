"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { EducationItem, EmploymentItem, Profile } from "@/types/profile";

interface ProfileData {
  profile: Profile | null;
  education: EducationItem[];
  employment: EmploymentItem[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useProfileData(): ProfileData {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [education, setEducation] = useState<EducationItem[]>([]);
  const [employment, setEmployment] = useState<EmploymentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: tick is an intentional refetch trigger
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    async function fetchAll() {
      try {
        const [profileRes, eduRes, empRes] = await Promise.all([
          fetch("/api/profile/me", { credentials: "include" }),
          fetch("/api/profile/education", { credentials: "include" }),
          fetch("/api/profile/employment", { credentials: "include" }),
        ]);

        if (profileRes.status === 401 || profileRes.status === 403) {
          router.push("/login");
          return;
        }

        if (!profileRes.ok) {
          if (!cancelled)
            setError("Could not load your profile. Please refresh.");
          return;
        }

        const [profileData, eduData, empData] = await Promise.all([
          profileRes.json(),
          eduRes.ok ? eduRes.json() : [],
          empRes.ok ? empRes.json() : [],
        ]);

        if (!cancelled) {
          setProfile(profileData);
          setEducation(eduData);
          setEmployment(empData);
        }
      } catch {
        if (!cancelled)
          setError("Unable to reach the server. Please check your connection.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    fetchAll();
    return () => {
      cancelled = true;
    };
  }, [router, tick]);

  return { profile, education, employment, isLoading, error, refetch };
}
