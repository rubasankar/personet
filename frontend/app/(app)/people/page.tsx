"use client";

import { useState } from "react";
import { PersonCard } from "@/components/people/PersonCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { usePeopleSearch } from "@/hooks/usePeopleSearch";

export default function PeoplePage() {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [company, setCompany] = useState("");
  const [institution, setInstitution] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const {
    results,
    isLoading,
    error,
    hasSearched,
    search,
    introLoading,
    intros,
    findIntro,
  } = usePeopleSearch();

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!name.trim()) return;
    search({
      name: name.trim(),
      location: location.trim() || undefined,
      company: company.trim() || undefined,
      institution: institution.trim() || undefined,
    });
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            People
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Search by name to find people, connect with them, or discover how to
            reach them.
          </p>
        </div>

        {/* Search form */}
        <div className="rounded-2xl bg-white px-6 py-6 shadow-sm ring-1 ring-gray-200">
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label
                htmlFor="people-name"
                className="block text-sm font-medium text-gray-700"
              >
                Name
              </label>
              <div className="mt-1 flex gap-2">
                <input
                  id="people-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                  placeholder="e.g. Alice"
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm outline-none transition placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isLoading || !name.trim()}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isLoading ? (
                    <>
                      <Spinner size="h-4 w-4" color="text-white" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    "Search"
                  )}
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowFilters((f) => !f)}
              className="text-xs font-medium text-indigo-600 hover:underline focus:outline-none"
            >
              {showFilters
                ? "Hide filters ▲"
                : "Filter by location, company or institution ▼"}
            </button>

            {showFilters && (
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label
                    htmlFor="people-location"
                    className="block text-xs font-medium text-gray-600"
                  >
                    Location
                  </label>
                  <input
                    id="people-location"
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    disabled={isLoading}
                    placeholder="e.g. London"
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm outline-none transition placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  />
                </div>
                <div>
                  <label
                    htmlFor="people-company"
                    className="block text-xs font-medium text-gray-600"
                  >
                    Company
                  </label>
                  <input
                    id="people-company"
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    disabled={isLoading}
                    placeholder="e.g. Acme"
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm outline-none transition placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  />
                </div>
                <div>
                  <label
                    htmlFor="people-institution"
                    className="block text-xs font-medium text-gray-600"
                  >
                    Institution
                  </label>
                  <input
                    id="people-institution"
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    disabled={isLoading}
                    placeholder="e.g. MIT"
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm outline-none transition placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  />
                </div>
              </div>
            )}
          </form>
        </div>

        {error && <ErrorBanner message={error} />}

        {/* Results */}
        {hasSearched &&
          !isLoading &&
          (results.length === 0 ? (
            <div className="rounded-xl bg-white px-6 py-10 text-center shadow-sm ring-1 ring-gray-200">
              <p className="text-sm text-gray-500">
                No people found matching your search.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-gray-500">
                {results.length} result{results.length !== 1 ? "s" : ""} - click{" "}
                <strong>How to reach</strong> on any person to see the best way
                to connect with them.
              </p>
              {results.map((person) => (
                <PersonCard
                  key={person.id}
                  person={person}
                  intro={intros[person.id]}
                  introLoading={introLoading === person.id}
                  onFindIntro={() => findIntro(person.id)}
                />
              ))}
            </div>
          ))}

        {!hasSearched && !isLoading && !error && (
          <div className="rounded-xl bg-white px-6 py-10 text-center shadow-sm ring-1 ring-gray-200">
            <p className="text-sm text-gray-400">
              Enter a name above to find people in the network.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
