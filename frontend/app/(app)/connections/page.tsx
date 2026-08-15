"use client";

import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type {
  Closeness,
  ConnectionContext,
  ConnectionItem,
} from "@/types/network";

// ─── Edit form state ───────────────────────────────────────────────────────

interface EditState {
  context: ConnectionContext;
  closeness: Closeness;
  since: string;
  saving: boolean;
  error: string;
  success: boolean;
}

function makeEditState(item: ConnectionItem): EditState {
  return {
    context: item.context as ConnectionContext,
    closeness: item.closeness as Closeness,
    since: item.since ?? "",
    saving: false,
    error: "",
    success: false,
  };
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

// ─── Connection card ──────────────────────────────────────────────────────

interface ConnectionCardProps {
  item: ConnectionItem;
  onDisconnected: () => void;
  onUpdated: (updated: ConnectionItem) => void;
}

function ConnectionCard({
  item,
  onDisconnected,
  onUpdated,
}: ConnectionCardProps) {
  const [editState, setEditState] = useState<EditState | null>(null);
  const [disconnecting, setDisconnecting] = useState(false);
  const [disconnectError, setDisconnectError] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);

  async function handleDisconnect() {
    setDisconnecting(true);
    setDisconnectError("");
    try {
      const res = await fetch(`/api/network/connect/${item.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        onDisconnected();
        return;
      }
      if (res.status === 404) {
        setDisconnectError("Connection not found.");
        return;
      }
      setDisconnectError("Could not remove connection. Please try again.");
    } catch {
      setDisconnectError("Network error. Please try again.");
    } finally {
      setDisconnecting(false);
      setShowConfirm(false);
    }
  }

  async function handleSave() {
    if (!editState) return;
    setEditState(
      (prev) => prev && { ...prev, saving: true, error: "", success: false },
    );

    try {
      const body: Record<string, string | null> = {
        context: editState.context,
        closeness: editState.closeness,
        since: editState.since.trim() || null,
      };

      const res = await fetch(`/api/network/connect/${item.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const updated: ConnectionItem = await res.json();
        setEditState(
          (prev) => prev && { ...prev, saving: false, success: true },
        );
        onUpdated(updated);
        setTimeout(() => setEditState(null), 800);
        return;
      }
      if (res.status === 404) {
        setEditState(
          (prev) =>
            prev && { ...prev, saving: false, error: "Connection not found." },
        );
        return;
      }
      setEditState(
        (prev) =>
          prev && {
            ...prev,
            saving: false,
            error: "Could not save. Please try again.",
          },
      );
    } catch {
      setEditState(
        (prev) =>
          prev && {
            ...prev,
            saving: false,
            error: "Network error. Please try again.",
          },
      );
    }
  }

  const closenessColor =
    item.closeness === "close"
      ? "bg-amber-50 text-amber-700 ring-amber-200"
      : "bg-gray-100 text-gray-600 ring-gray-200";

  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-900">
            {item.name}
          </p>
          {item.location && (
            <p className="mt-0.5 text-xs text-gray-500">{item.location}</p>
          )}
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            <span className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-indigo-200 capitalize">
              {item.context}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 capitalize ${closenessColor}`}
            >
              {item.closeness}
            </span>
            {item.since && (
              <span className="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5 text-xs text-gray-500 ring-1 ring-gray-200">
                Since {item.since}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-shrink-0 gap-1.5">
          {editState ? (
            <button
              type="button"
              onClick={() => setEditState(null)}
              className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-100"
            >
              Cancel
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setEditState(makeEditState(item))}
              disabled={disconnecting}
              className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-indigo-600 transition hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
            >
              Edit
            </button>
          )}

          {!showConfirm ? (
            <button
              type="button"
              onClick={() => setShowConfirm(true)}
              disabled={disconnecting || !!editState}
              className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:opacity-50"
            >
              Remove
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-600">Sure?</span>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="flex items-center gap-1 rounded-lg bg-red-600 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-60"
              >
                {disconnecting && <Spinner size="h-3 w-3" color="text-white" />}
                Yes
              </button>
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-100"
              >
                No
              </button>
            </div>
          )}
        </div>
      </div>

      {disconnectError && (
        <div className="px-4 pb-3">
          <ErrorBanner message={disconnectError} />
        </div>
      )}

      {/* Inline edit form */}
      {editState && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSave();
          }}
          className="border-t border-gray-100 px-4 pb-4 pt-3 space-y-3"
        >
          {editState.success && <SuccessBanner message="Saved!" />}
          {editState.error && <ErrorBanner message={editState.error} />}

          <div className="flex flex-wrap gap-3">
            <div>
              <label
                htmlFor={`edit-ctx-${item.id}`}
                className="block text-xs font-medium text-gray-600"
              >
                How you know them
              </label>
              <select
                id={`edit-ctx-${item.id}`}
                value={editState.context}
                onChange={(e) =>
                  setEditState(
                    (prev) =>
                      prev && {
                        ...prev,
                        context: e.target.value as ConnectionContext,
                      },
                  )
                }
                disabled={editState.saving}
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
                htmlFor={`edit-cls-${item.id}`}
                className="block text-xs font-medium text-gray-600"
              >
                Closeness
              </label>
              <select
                id={`edit-cls-${item.id}`}
                value={editState.closeness}
                onChange={(e) =>
                  setEditState(
                    (prev) =>
                      prev && {
                        ...prev,
                        closeness: e.target.value as Closeness,
                      },
                  )
                }
                disabled={editState.saving}
                className="mt-1 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
              >
                {CLOSENESS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor={`edit-since-${item.id}`}
                className="block text-xs font-medium text-gray-600"
              >
                Since{" "}
                <span className="text-gray-400">(optional, YYYY-MM-DD)</span>
              </label>
              <input
                id={`edit-since-${item.id}`}
                type="date"
                value={editState.since}
                onChange={(e) =>
                  setEditState(
                    (prev) => prev && { ...prev, since: e.target.value },
                  )
                }
                disabled={editState.saving}
                className="mt-1 rounded-lg border border-gray-300 bg-white px-2 py-1.5 text-xs shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={editState.saving}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
          >
            {editState.saving && <Spinner size="h-3 w-3" color="text-white" />}
            {editState.saving ? "Saving..." : "Save"}
          </button>
        </form>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<ConnectionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchConnections = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch("/api/network/connections", {
        credentials: "include",
      });
      if (!res.ok) {
        setError("Could not load connections. Please refresh.");
        return;
      }
      const data: ConnectionItem[] = await res.json();
      setConnections(data);
    } catch {
      setError("Unable to reach the server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  function handleDisconnected(id: string) {
    setConnections((prev) => prev.filter((c) => c.id !== id));
  }

  function handleUpdated(updated: ConnectionItem) {
    setConnections((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c)),
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Connections
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Your direct connections - edit relationship details or remove
            connections here.
          </p>
        </div>

        {error && <ErrorBanner message={error} />}

        {isLoading ? (
          <div className="space-y-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : connections.length === 0 ? (
          <div className="rounded-xl bg-white px-6 py-12 text-center shadow-sm ring-1 ring-gray-200">
            <p className="text-sm text-gray-500">No connections yet.</p>
            <p className="mt-1 text-xs text-gray-400">
              Search for people on the People page and connect with them.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-gray-500">
              {connections.length} connection
              {connections.length !== 1 ? "s" : ""}
            </p>
            {connections.map((c) => (
              <ConnectionCard
                key={c.id}
                item={c}
                onDisconnected={() => handleDisconnected(c.id)}
                onUpdated={handleUpdated}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
