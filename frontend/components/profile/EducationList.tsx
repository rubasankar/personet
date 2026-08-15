"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type {
  EducationItem,
  EducationUpdateFieldErrors,
} from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

interface EducationListProps {
  items: EducationItem[];
  onChanged: () => void;
}

interface EditState {
  degree: string;
  department: string;
  end_year: string;
  saving: boolean;
  errors: EducationUpdateFieldErrors;
  serviceError: string;
  success: boolean;
}

function makeEditState(item: EducationItem): EditState {
  return {
    degree: item.degree,
    department: item.department,
    end_year: String(item.end_year),
    saving: false,
    errors: {},
    serviceError: "",
    success: false,
  };
}

export function EducationList({ items, onChanged }: EducationListProps) {
  // key -> edit state; null means not editing
  const [editing, setEditing] = useState<Record<string, EditState>>({});
  const [deletingKey, setDeletingKey] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState("");

  function startEdit(item: EducationItem) {
    const key = `${item.institution_name}-${item.start_year}`;
    setEditing((prev) => ({ ...prev, [key]: makeEditState(item) }));
  }

  function cancelEdit(key: string) {
    setEditing((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function updateField(key: string, field: keyof EditState, value: string) {
    setEditing((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }));
  }

  async function handleSave(item: EducationItem) {
    const key = `${item.institution_name}-${item.start_year}`;
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
      const body: Record<string, string | number> = {};
      if (state.degree.trim()) body.degree = state.degree.trim();
      if (state.department.trim()) body.department = state.department.trim();
      if (state.end_year.trim()) body.end_year = parseInt(state.end_year, 10);

      const res = await fetch(
        `/api/profile/education/${encodeURIComponent(item.institution_name)}/${item.start_year}`,
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
            errors: parseValidationErrors(detail) as EducationUpdateFieldErrors,
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

  async function handleDelete(institutionName: string, startYear: number) {
    const key = `${institutionName}-${startYear}`;
    setDeletingKey(key);
    setDeleteError("");

    try {
      const res = await fetch(
        `/api/profile/education/${encodeURIComponent(institutionName)}/${startYear}`,
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
        No education records yet. Add one below.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {deleteError && <ErrorBanner message={deleteError} />}

      {items.map((item) => {
        const key = `${item.institution_name}-${item.start_year}`;
        const editState = editing[key];
        const isDeleting = deletingKey === key;

        return (
          <div key={key} className="rounded-xl bg-gray-50 ring-1 ring-gray-200">
            {/* Row header - always visible */}
            <div className="flex items-start justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900">
                  {item.institution_name}
                </p>
                <p className="text-xs text-gray-600">
                  {item.degree} · {item.department}
                </p>
                <p className="text-xs text-gray-500">
                  {item.start_year} - {item.end_year}
                  <span className="ml-2 capitalize text-gray-400">
                    ({item.institution_type})
                  </span>
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
                    handleDelete(item.institution_name, item.start_year)
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
                      htmlFor={`${key}-degree`}
                      className="block text-xs font-medium text-gray-600"
                    >
                      Degree
                    </label>
                    <input
                      id={`${key}-degree`}
                      type="text"
                      value={editState.degree}
                      onChange={(e) =>
                        updateField(key, "degree", e.target.value)
                      }
                      disabled={editState.saving}
                      aria-invalid={!!editState.errors.degree}
                      className={fieldClass(!!editState.errors.degree)}
                    />
                    <FieldError
                      id={`${key}-degree-err`}
                      message={editState.errors.degree}
                    />
                  </div>

                  <div>
                    <label
                      htmlFor={`${key}-department`}
                      className="block text-xs font-medium text-gray-600"
                    >
                      Department
                    </label>
                    <input
                      id={`${key}-department`}
                      type="text"
                      value={editState.department}
                      onChange={(e) =>
                        updateField(key, "department", e.target.value)
                      }
                      disabled={editState.saving}
                      aria-invalid={!!editState.errors.department}
                      className={fieldClass(!!editState.errors.department)}
                    />
                    <FieldError
                      id={`${key}-dept-err`}
                      message={editState.errors.department}
                    />
                  </div>

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
