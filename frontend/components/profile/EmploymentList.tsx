"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type {
  EmploymentItem,
  EmploymentUpdateFieldErrors,
} from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

interface EmploymentListProps {
  items: EmploymentItem[];
  onChanged: () => void;
}

interface EditState {
  role: string;
  end_year: string;
  is_current: boolean;
  saving: boolean;
  errors: EmploymentUpdateFieldErrors;
  serviceError: string;
  success: boolean;
}

function makeEditState(item: EmploymentItem): EditState {
  return {
    role: item.role,
    end_year: item.end_year !== null ? String(item.end_year) : "",
    is_current: item.is_current,
    saving: false,
    errors: {},
    serviceError: "",
    success: false,
  };
}

export function EmploymentList({ items, onChanged }: EmploymentListProps) {
  const [editing, setEditing] = useState<Record<string, EditState>>({});
  const [deletingKey, setDeletingKey] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState("");

  function startEdit(item: EmploymentItem) {
    const key = `${item.company_name}-${item.start_year}`;
    setEditing((prev) => ({ ...prev, [key]: makeEditState(item) }));
  }

  function cancelEdit(key: string) {
    setEditing((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function updateField(
    key: string,
    field: keyof EditState,
    value: string | boolean,
  ) {
    setEditing((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }));
  }

  function toggleCurrent(key: string) {
    setEditing((prev) => {
      const wasCurrentl = prev[key].is_current;
      return {
        ...prev,
        [key]: {
          ...prev[key],
          is_current: !wasCurrentl,
          end_year: !wasCurrentl ? "" : prev[key].end_year,
        },
      };
    });
  }

  async function handleSave(item: EmploymentItem) {
    const key = `${item.company_name}-${item.start_year}`;
    const state = editing[key];
    if (!state) return;

    setEditing((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        saving: true,
        errors: {},
        serviceError: "",
        success: false,
      },
    }));

    try {
      const body: Record<string, string | number | boolean | null> = {
        is_current: state.is_current,
      };
      if (state.role.trim()) body.role = state.role.trim();
      if (!state.is_current && state.end_year.trim()) {
        body.end_year = parseInt(state.end_year, 10);
      }
      if (state.is_current) {
        body.end_year = null;
      }

      const res = await fetch(
        `/api/profile/employment/${encodeURIComponent(item.company_name)}/${item.start_year}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(body),
        },
      );

      if (res.ok) {
        setEditing((prev) => ({
          ...prev,
          [key]: { ...prev[key], success: true, saving: false },
        }));
        setTimeout(() => cancelEdit(key), 800);
        onChanged();
        return;
      }

      if (res.status === 422) {
        const data = await res.json();
        const detail: FastAPIValidationError[] = data.detail ?? [];
        setEditing((prev) => ({
          ...prev,
          [key]: {
            ...prev[key],
            errors: parseValidationErrors(
              detail,
            ) as EmploymentUpdateFieldErrors,
            saving: false,
          },
        }));
        return;
      }

      if (res.status === 404) {
        setEditing((prev) => ({
          ...prev,
          [key]: {
            ...prev[key],
            serviceError: "Record not found.",
            saving: false,
          },
        }));
        return;
      }

      setEditing((prev) => ({
        ...prev,
        [key]: {
          ...prev[key],
          serviceError: "Could not save. Please try again.",
          saving: false,
        },
      }));
    } catch {
      setEditing((prev) => ({
        ...prev,
        [key]: {
          ...prev[key],
          serviceError: "Network error. Please try again.",
          saving: false,
        },
      }));
    }
  }

  async function handleDelete(companyName: string, startYear: number) {
    const key = `${companyName}-${startYear}`;
    setDeletingKey(key);
    setDeleteError("");

    try {
      const res = await fetch(
        `/api/profile/employment/${encodeURIComponent(companyName)}/${startYear}`,
        { method: "DELETE", credentials: "include" },
      );

      if (res.status === 204) {
        onChanged();
        return;
      }
      setDeleteError(
        res.status === 404
          ? "Record not found."
          : "Could not delete. Please try again.",
      );
    } catch {
      setDeleteError("Network error. Please try again.");
    } finally {
      setDeletingKey(null);
    }
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No employment records yet. Add one below.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {deleteError && <ErrorBanner message={deleteError} />}

      {items.map((item) => {
        const key = `${item.company_name}-${item.start_year}`;
        const editState = editing[key];
        const isDeleting = deletingKey === key;

        return (
          <div key={key} className="rounded-xl bg-gray-50 ring-1 ring-gray-200">
            {/* Row header - always visible */}
            <div className="flex items-start justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900">
                  {item.company_name}
                </p>
                <p className="text-xs text-gray-600">{item.role}</p>
                <p className="text-xs text-gray-500">
                  {item.start_year} -{" "}
                  {item.is_current ? "Present" : (item.end_year ?? "?")}
                  {item.is_current && (
                    <span className="ml-2 rounded-full bg-green-50 px-1.5 py-0.5 text-xs text-green-700 ring-1 ring-green-200">
                      Current
                    </span>
                  )}
                </p>
              </div>

              <div className="flex flex-shrink-0 gap-1.5">
                {editState ? (
                  <button
                    type="button"
                    onClick={() => cancelEdit(key)}
                    className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
                  >
                    Cancel
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => startEdit(item)}
                    disabled={isDeleting}
                    className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-indigo-600 transition hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
                  >
                    Edit
                  </button>
                )}
                <button
                  type="button"
                  onClick={() =>
                    handleDelete(item.company_name, item.start_year)
                  }
                  disabled={isDeleting || !!editState}
                  className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:opacity-50"
                >
                  {isDeleting ? (
                    <Spinner size="h-3 w-3" color="text-red-500" />
                  ) : (
                    "Remove"
                  )}
                </button>
              </div>
            </div>

            {/* Inline edit form */}
            {editState && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSave(item);
                }}
                noValidate
                className="border-t border-gray-200 px-4 pb-4 pt-3 space-y-3"
              >
                {editState.success && <SuccessBanner message="Saved!" />}
                {editState.serviceError && (
                  <ErrorBanner message={editState.serviceError} />
                )}

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label
                      htmlFor={`${key}-role`}
                      className="block text-xs font-medium text-gray-600"
                    >
                      Role
                    </label>
                    <input
                      id={`${key}-role`}
                      type="text"
                      value={editState.role}
                      onChange={(e) => updateField(key, "role", e.target.value)}
                      disabled={editState.saving}
                      aria-invalid={!!editState.errors.role}
                      className={fieldClass(!!editState.errors.role)}
                    />
                    <FieldError
                      id={`${key}-role-err`}
                      message={editState.errors.role}
                    />
                  </div>

                  {!editState.is_current && (
                    <div>
                      <label
                        htmlFor={`${key}-endyear`}
                        className="block text-xs font-medium text-gray-600"
                      >
                        End year
                      </label>
                      <input
                        id={`${key}-endyear`}
                        type="number"
                        value={editState.end_year}
                        onChange={(e) =>
                          updateField(key, "end_year", e.target.value)
                        }
                        disabled={editState.saving}
                        min={1900}
                        aria-invalid={!!editState.errors.end_year}
                        className={fieldClass(!!editState.errors.end_year)}
                      />
                      <FieldError
                        id={`${key}-endyr-err`}
                        message={editState.errors.end_year}
                      />
                    </div>
                  )}
                </div>

                {/* Current role toggle */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={editState.is_current}
                    onClick={() => toggleCurrent(key)}
                    disabled={editState.saving}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 ${
                      editState.is_current ? "bg-indigo-600" : "bg-gray-200"
                    }`}
                  >
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        editState.is_current ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                  <span className="text-xs font-medium text-gray-600">
                    I currently work here
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={editState.saving}
                  className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
                >
                  {editState.saving && (
                    <Spinner size="h-3 w-3" color="text-white" />
                  )}
                  {editState.saving ? "Saving..." : "Save"}
                </button>
              </form>
            )}
          </div>
        );
      })}
    </div>
  );
}
