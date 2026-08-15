"use client";

import { useCallback, useState } from "react";
import type { IntroResponse, UserSearchItem } from "@/types/network";

interface SearchFilters {
  name: string;
  location?: string;
  company?: string;
  institution?: string;
}

interface UsePeopleSearchReturn {
  results: UserSearchItem[];
  isLoading: boolean;
  error: string;
  hasSearched: boolean;
  search: (filters: SearchFilters) => Promise<void>;
  clearResults: () => void;
  introLoading: string | null;
  intros: Record<string, IntroResponse>;
  findIntro: (personId: string) => Promise<void>;
}

export function usePeopleSearch(): UsePeopleSearchReturn {
  const [results, setResults] = useState<UserSearchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [introLoading, setIntroLoading] = useState<string | null>(null);
  const [intros, setIntros] = useState<Record<string, IntroResponse>>({});

  function clearResults() {
    setResults([]);
    setError("");
    setHasSearched(false);
    setIntros({});
  }

  const search = useCallback(async (filters: SearchFilters) => {
    const params = new URLSearchParams({ name: filters.name });
    if (filters.location) params.set("location", filters.location);
    if (filters.company) params.set("company", filters.company);
    if (filters.institution) params.set("institution", filters.institution);

    setError("");
    setIsLoading(true);
    setHasSearched(false);
    setIntros({});

    try {
      const res = await fetch(`/api/network/users?${params.toString()}`, {
        credentials: "include",
      });

      if (res.status === 503) {
        setError(
          "The service is temporarily unavailable. Please try again later.",
        );
        return;
      }
      if (!res.ok) {
        setError("Something went wrong. Please try again.");
        return;
      }

      const data: UserSearchItem[] = await res.json();
      const seen = new Set<string>();
      const unique = data.filter((p) => {
        if (seen.has(p.id)) return false;
        seen.add(p.id);
        return true;
      });
      setResults(unique);
      setHasSearched(true);
    } catch {
      setError("Unable to reach the server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const findIntro = useCallback(
    async (personId: string) => {
      // Toggle off if already loaded
      if (intros[personId] !== undefined) {
        setIntros((prev) => {
          const next = { ...prev };
          delete next[personId];
          return next;
        });
        return;
      }

      setIntroLoading(personId);
      try {
        const res = await fetch(
          `/api/network/intro/${encodeURIComponent(personId)}`,
          {
            credentials: "include",
          },
        );

        if (res.ok) {
          const data: IntroResponse = await res.json();
          setIntros((prev) => ({ ...prev, [personId]: data }));
        }
        // silent on error - card still works
      } catch {
        // silent
      } finally {
        setIntroLoading(null);
      }
    },
    [intros],
  );

  return {
    results,
    isLoading,
    error,
    hasSearched,
    search,
    clearResults,
    introLoading,
    intros,
    findIntro,
  };
}
