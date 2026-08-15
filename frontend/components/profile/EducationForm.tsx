"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type { EducationFieldErrors } from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

const EMPTY = {
  institution_name: "",
  institution_type: "" as "" | "university" | "school" | "college",
  degree: "",
  department: "",
  start_year: "",
  end_year: "",
};

export function EducationForm({ onAdded }: { onAdded?: () => void } = {}) {
  const [fields, setFields] = useState(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<EducationFieldErrors>({});
  const [serviceError, setServiceError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  function clearStatus() {
    setFieldErrors({});
    setServiceError("");
    setSuccess(false);
  }

  function setField(key: keyof typeof EMPTY, value: string) {
    setFields((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    clearStatus();
    setIsLoading(true);

    try {
      const body = {
        institution_name: fields.institution_name,
        institution_type: fields.institution_type,
        degree: fields.degree,
        department: fields.department,
        start_year: parseInt(fields.start_year, 10),
        end_year: parseInt(fields.end_year, 10),
      };

      const res = await fetch("/api/profile/education", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (res.status === 201) {
        setSuccess(true);
        setFields(EMPTY);
        onAdded?.();
        return;
      }

      if (res.status === 422) {
        const data = await res.json();
        const detail: FastAPIValidationError[] = data.detail ?? [];
        setFieldErrors(parseValidationErrors(detail) as EducationFieldErrors);
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
        "Unable to reach the server. Please check your connection and try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section
      aria-labelledby="education-heading"
      className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-gray-200"
    >
      <h2
        id="education-heading"
        className="mb-6 text-lg font-semibold text-gray-900"
      >
        Add Education
      </h2>

      {success && (
        <div className="mb-5">
          <SuccessBanner message="Education entry added successfully." />
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
            htmlFor="edu-institution-name"
            className="block text-sm font-medium text-gray-700"
          >
            Institution name
          </label>
          <input
            id="edu-institution-name"
            type="text"
            value={fields.institution_name}
            onChange={(e) => setField("institution_name", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.institution_name
                ? "edu-institution-name-error"
                : undefined
            }
            aria-invalid={!!fieldErrors.institution_name}
            className={fieldClass(!!fieldErrors.institution_name)}
            placeholder="e.g. MIT"
          />
          <FieldError
            id="edu-institution-name-error"
            message={fieldErrors.institution_name}
          />
        </div>

        <div>
          <label
            htmlFor="edu-institution-type"
            className="block text-sm font-medium text-gray-700"
          >
            Institution type
          </label>
          <select
            id="edu-institution-type"
            value={fields.institution_type}
            onChange={(e) => setField("institution_type", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.institution_type
                ? "edu-institution-type-error"
                : undefined
            }
            aria-invalid={!!fieldErrors.institution_type}
            className={fieldClass(!!fieldErrors.institution_type)}
          >
            <option value="" disabled>
              Select a type...
            </option>
            <option value="university">University</option>
            <option value="school">School</option>
            <option value="college">College</option>
          </select>
          <FieldError
            id="edu-institution-type-error"
            message={fieldErrors.institution_type}
          />
        </div>

        <div>
          <label
            htmlFor="edu-degree"
            className="block text-sm font-medium text-gray-700"
          >
            Degree
          </label>
          <input
            id="edu-degree"
            type="text"
            value={fields.degree}
            onChange={(e) => setField("degree", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.degree ? "edu-degree-error" : undefined
            }
            aria-invalid={!!fieldErrors.degree}
            className={fieldClass(!!fieldErrors.degree)}
            placeholder="e.g. BSc Computer Science"
          />
          <FieldError id="edu-degree-error" message={fieldErrors.degree} />
        </div>

        <div>
          <label
            htmlFor="edu-department"
            className="block text-sm font-medium text-gray-700"
          >
            Department
          </label>
          <input
            id="edu-department"
            type="text"
            value={fields.department}
            onChange={(e) => setField("department", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.department ? "edu-department-error" : undefined
            }
            aria-invalid={!!fieldErrors.department}
            className={fieldClass(!!fieldErrors.department)}
            placeholder="e.g. School of Engineering"
          />
          <FieldError
            id="edu-department-error"
            message={fieldErrors.department}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="edu-start-year"
              className="block text-sm font-medium text-gray-700"
            >
              Start year
            </label>
            <input
              id="edu-start-year"
              type="number"
              value={fields.start_year}
              onChange={(e) => setField("start_year", e.target.value)}
              disabled={isLoading}
              aria-describedby={
                fieldErrors.start_year ? "edu-start-year-error" : undefined
              }
              aria-invalid={!!fieldErrors.start_year}
              className={fieldClass(!!fieldErrors.start_year)}
              placeholder="e.g. 2018"
              min={1900}
              max={new Date().getFullYear()}
            />
            <FieldError
              id="edu-start-year-error"
              message={fieldErrors.start_year}
            />
          </div>

          <div>
            <label
              htmlFor="edu-end-year"
              className="block text-sm font-medium text-gray-700"
            >
              End year
            </label>
            <input
              id="edu-end-year"
              type="number"
              value={fields.end_year}
              onChange={(e) => setField("end_year", e.target.value)}
              disabled={isLoading}
              aria-describedby={
                fieldErrors.end_year ? "edu-end-year-error" : undefined
              }
              aria-invalid={!!fieldErrors.end_year}
              className={fieldClass(!!fieldErrors.end_year)}
              placeholder="e.g. 2022"
              min={1900}
              max={new Date().getFullYear() + 10}
            />
            <FieldError
              id="edu-end-year-error"
              message={fieldErrors.end_year}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading && <Spinner size="h-4 w-4" color="text-white" />}
          {isLoading ? "Saving..." : "Save education"}
        </button>
      </form>
    </section>
  );
}
