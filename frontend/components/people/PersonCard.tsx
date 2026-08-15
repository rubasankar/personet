"use client";

import { useState } from "react";
import { PathResult } from "@/components/search/PathResult";
import { Spinner } from "@/components/ui/Spinner";
import type {
  Closeness,
  ConnectionContext,
  IntroResponse,
  IntroSuggestion,
  UserSearchItem,
} from "@/types/network";

interface PersonCardProps {
  person: UserSearchItem;
  intro?: IntroResponse;
  introLoading?: boolean;
  onFindIntro?: () => void;
}

const CONTEXT_OPTIONS: { value: ConnectionContext; label: string }[] = [
  { value: "colleague", label: "Colleague" },
  { value: "classmate", label: "Classmate" },
  { value: "friend", label: "Friend" },
  { value: "family", label: "Family" },
];

const CLOSENESS_OPTIONS: { value: Closeness; label: string }[] = [
  { value: "acquaintance", label: "Acquaintance" },
  { value: "close", label: "Close" },
];

// ─── Shared helpers ────────────────────────────────────────────────────────

function SharedContextBadges({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((ctx) => (
        <span
          key={ctx}
          className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 ring-1 ring-green-200"
        >
          {ctx}
        </span>
      ))}
    </div>
  );
}

function SuggestionCards({ suggestions }: { suggestions: IntroSuggestion[] }) {
  if (suggestions.length === 0) return null;
  return (
    <div className="space-y-3">
      {suggestions.map((s) => {
        const nodeLabel =
          s.shared_node_type === "Company" ? "works at" : "studied at";

        // Build the full visual chain:
        // reach_type="context": [You] --[share Acme]--> [Alice] -> Charlie -> Bob
        // reach_type="knows":   [You] -> ... -> [Alice] --[share Acme w/ target]--> Charlie -> Bob
        const chainLabels = s.chain_to_target.map((n, i) => ({
          key: i === 0 ? `bridge-${s.id}` : n.id,
          text: n.name,
          isFirst: i === 0,
          isLast: i === s.chain_to_target.length - 1,
        }));

        return (
          <div
            key={s.id}
            className="rounded-lg bg-amber-50 px-3 py-3 ring-1 ring-amber-200"
          >
            {/* Bridge person header */}
            <div className="mb-2">
              <p className="text-xs font-semibold text-gray-900">{s.name}</p>
              {s.location && (
                <p className="text-xs text-gray-500">{s.location}</p>
              )}
              <p className="text-xs text-amber-700">
                Also {nodeLabel} <strong>{s.shared_node_name}</strong>
                {s.reach_type === "context"
                  ? " - same as you"
                  : s.knows_distance === 1
                    ? " - your direct connection"
                    : ` - ${s.knows_distance} hops from you`}
              </p>
            </div>

            {/* Onward path from bridge -> target */}
            {chainLabels.length > 1 && (
              <div>
                <p className="mb-1.5 text-xs font-medium text-amber-600">
                  Their path to the target:
                </p>
                <div className="flex flex-wrap items-center gap-1.5">
                  {chainLabels.map(({ key, text, isFirst, isLast }, idx) => (
                    <span key={key} className="flex items-center gap-1.5">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          isFirst
                            ? "bg-amber-100 text-amber-800 ring-1 ring-amber-300"
                            : isLast
                              ? "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-300"
                              : "bg-white text-gray-700 ring-1 ring-gray-300"
                        }`}
                      >
                        {text}
                      </span>
                      {idx < chainLabels.length - 1 && (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          className="h-3.5 w-3.5 flex-shrink-0 text-amber-400"
                          aria-hidden="true"
                        >
                          <path
                            fillRule="evenodd"
                            d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Intro result renderer ─────────────────────────────────────────────────

function IntroPanel({ intro }: { intro: IntroResponse }) {
  if (intro.type === "direct_context") {
    return (
      <div className="space-y-2.5">
        <p className="text-xs font-semibold text-green-700">
          You share common ground - reach out directly!
        </p>
        <SharedContextBadges items={intro.shared_context} />
        <p className="text-xs text-gray-500">
          Mention your shared connection when you message them.
        </p>
        {intro.suggestions.length > 0 && (
          <>
            <p className="text-xs font-semibold text-amber-700 pt-1">
              Connect with one of these people to reach further into their
              network:
            </p>
            <SuggestionCards suggestions={intro.suggestions} />
          </>
        )}
      </div>
    );
  }

  if (intro.type === "knows_path") {
    return (
      <div className="space-y-3">
        {intro.shared_context.length > 0 && (
          <div className="rounded-lg bg-green-50 px-3 py-2.5 ring-1 ring-green-200">
            <p className="mb-1.5 text-xs font-semibold text-green-700">
              You also share common ground - mention it for a warmer intro:
            </p>
            <SharedContextBadges items={intro.shared_context} />
          </div>
        )}
        <PathResult nodes={intro.chain} viaCloseOnly={intro.via_close_only} />
      </div>
    );
  }

  if (intro.type === "suggested_intro") {
    return (
      <div className="space-y-2.5">
        <p className="text-xs font-semibold text-amber-700">
          No direct path yet. Connect with one of these people first - here's
          the route they have to the target:
        </p>
        <SuggestionCards suggestions={intro.suggestions} />
        <p className="text-xs text-gray-400">
          Once connected, ask them to make the introduction.
        </p>
      </div>
    );
  }

  // unreachable
  return (
    <p className="text-xs text-gray-500">
      No connection path or shared context found. Add more education and
      employment to your profile to expand your reachable network.
    </p>
  );
}

// ─── Main card ─────────────────────────────────────────────────────────────

export function PersonCard({
  person,
  intro,
  introLoading,
  onFindIntro,
}: PersonCardProps) {
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [connectError, setConnectError] = useState("");
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [context, setContext] = useState<ConnectionContext>("colleague");
  const [closeness, setCloseness] = useState<Closeness>("acquaintance");

  async function handleConnect() {
    setConnecting(true);
    setConnectError("");
    try {
      const res = await fetch(`/api/network/connect/${person.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ context, closeness }),
      });

      if (res.status === 201) {
        setConnected(true);
        setShowConnectForm(false);
        return;
      }
      if (res.status === 400) {
        setConnectError("You can't connect with yourself.");
        return;
      }
      setConnectError("Could not connect. Please try again.");
    } catch {
      setConnectError("Network error. Please try again.");
    } finally {
      setConnecting(false);
    }
  }

  const introVisible = intro !== undefined;

  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
      {/* Main row */}
      <div className="flex items-start gap-4 p-4">
        {/* Info */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-gray-900">
            {person.name}
          </p>
          {person.location && (
            <p className="mt-0.5 text-xs text-gray-500">{person.location}</p>
          )}
          {(person.companies.length > 0 || person.institutions.length > 0) && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {person.companies.map((c) => (
                <span
                  key={c}
                  className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700 ring-1 ring-blue-200"
                >
                  {c}
                </span>
              ))}
              {person.institutions.map((i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-full bg-purple-50 px-2 py-0.5 text-xs text-purple-700 ring-1 ring-purple-200"
                >
                  {i}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-shrink-0 flex-col items-end gap-2">
          {connected ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700 ring-1 ring-green-200">
              ✓ Connected
            </span>
          ) : (
            <button
              type="button"
              onClick={() => setShowConnectForm((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
                showConnectForm
                  ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  : "bg-indigo-600 text-white hover:bg-indigo-500"
              }`}
            >
              {showConnectForm ? "Cancel" : "Connect"}
            </button>
          )}

          {onFindIntro && (
            <button
              type="button"
              onClick={onFindIntro}
              disabled={introLoading}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50 ${
                introVisible
                  ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                  : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              }`}
            >
              {introLoading ? (
                <Spinner size="h-3 w-3" color="text-indigo-500" />
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-3.5 w-3.5"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {introVisible ? "Hide" : "How to reach"}
            </button>
          )}
        </div>
      </div>

      {/* Connect form */}
      {showConnectForm && !connected && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3">
          <div className="flex flex-wrap gap-3">
            <div>
              <label
                htmlFor={`ctx-${person.id}`}
                className="block text-xs font-medium text-gray-600"
              >
                How you know them
              </label>
              <select
                id={`ctx-${person.id}`}
                value={context}
                onChange={(e) =>
                  setContext(e.target.value as ConnectionContext)
                }
                className="mt-1 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
              >
                {CONTEXT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor={`cls-${person.id}`}
                className="block text-xs font-medium text-gray-600"
              >
                Closeness
              </label>
              <select
                id={`cls-${person.id}`}
                value={closeness}
                onChange={(e) => setCloseness(e.target.value as Closeness)}
                className="mt-1 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
              >
                {CLOSENESS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {connectError && (
            <p className="mt-2 text-xs text-red-600">{connectError}</p>
          )}
          <button
            type="button"
            onClick={handleConnect}
            disabled={connecting}
            className="mt-3 flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
          >
            {connecting && <Spinner size="h-3 w-3" color="text-white" />}
            {connecting ? "Connecting..." : "Confirm connection"}
          </button>
        </div>
      )}

      {/* Intro panel */}
      {introVisible && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3">
          <IntroPanel intro={intro} />
        </div>
      )}
    </div>
  );
}
