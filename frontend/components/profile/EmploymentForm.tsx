"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type { EmploymentFieldErrors } from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

const EMPTY = {
  company_name: "",
  role: "",
  start_year: "",
  end_year: "",
  is_current: false,
};

export function EmploymentForm({ onAdded }: { onAdded?: () => void } = {}) {
  const [fields, setFields] = useState(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<EmploymentFieldErrors>({});
  const [serviceError, setServiceError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  function clearStatus() {
    setFieldErrors({});
    setServiceError("");
    setSuccess(false);
  }

  function setField(key: keyof typeof EMPTY, value: string | boolean) {
    setFields((prev) => ({ ...prev, [key]: value }));
  }

  function handleCurrentToggle() {
    setFields((prev) => ({
      ...prev,
      is_current: !prev.is_current,
      end_year: !prev.is_current ? "" : prev.end_year,
    }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    clearStatus();
    setIsLoading(true);

    try {
      const body = {
        company_name: fields.company_name,
        role: fields.role,
        start_year: parseInt(fields.start_year, 10),
        end_year: fields.is_current
          ? null
          : fields.end_year
            ? parseInt(fields.end_year, 10)
            : null,
        is_current: fields.is_current,
      };

      const res = await fetch("/api/profile/employment", {
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
        setFieldErrors(parseValidationErrors(detail) as EmploymentFieldErrors);
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
      aria-labelledby="employment-heading"
      className="rounded-2xl bg-white px-8 py-8 shadow-sm ring-1 ring-gray-200"
    >
      <h2
        id="employment-heading"
        className="mb-6 text-lg font-semibold text-gray-900"
      >
        Add Employment
      </h2>

      {success && (
        <div className="mb-5">
          <SuccessBanner message="Employment entry added successfully." />
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
            htmlFor="emp-company-name"
            className="block text-sm font-medium text-gray-700"
          >
            Company name
          </label>
          <input
            id="emp-company-name"
            type="text"
            value={fields.company_name}
            onChange={(e) => setField("company_name", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.company_name ? "emp-company-name-error" : undefined
            }
            aria-invalid={!!fieldErrors.company_name}
            className={fieldClass(!!fieldErrors.company_name)}
            placeholder="e.g. Acme Corp"
          />
          <FieldError
            id="emp-company-name-error"
            message={fieldErrors.company_name}
          />
        </div>

        <div>
          <label
            htmlFor="emp-role"
            className="block text-sm font-medium text-gray-700"
          >
            Role
          </label>
          <input
            id="emp-role"
            type="text"
            value={fields.role}
            onChange={(e) => setField("role", e.target.value)}
            disabled={isLoading}
            aria-describedby={fieldErrors.role ? "emp-role-error" : undefined}
            aria-invalid={!!fieldErrors.role}
            className={fieldClass(!!fieldErrors.role)}
            placeholder="e.g. Software Engineer"
          />
          <FieldError id="emp-role-error" message={fieldErrors.role} />
        </div>

        <div>
          <label
            htmlFor="emp-start-year"
            className="block text-sm font-medium text-gray-700"
          >
            Start year
          </label>
          <input
            id="emp-start-year"
            type="number"
            value={fields.start_year}
            onChange={(e) => setField("start_year", e.target.value)}
            disabled={isLoading}
            aria-describedby={
              fieldErrors.start_year ? "emp-start-year-error" : undefined
            }
            aria-invalid={!!fieldErrors.start_year}
            className={fieldClass(!!fieldErrors.start_year)}
            placeholder="e.g. 2020"
            min={1900}
            max={new Date().getFullYear()}
          />
          <FieldError
            id="emp-start-year-error"
            message={fieldErrors.start_year}
          />
        </div>

        {!fields.is_current && (
          <div>
            <label
              htmlFor="emp-end-year"
              className="block text-sm font-medium text-gray-700"
            >
              End year
            </label>
            <input
              id="emp-end-year"
              type="number"
              value={fields.end_year}
              onChange={(e) => setField("end_year", e.target.value)}
              disabled={isLoading}
              aria-describedby={
                fieldErrors.end_year ? "emp-end-year-error" : undefined
              }
              aria-invalid={!!fieldErrors.end_year}
              className={fieldClass(!!fieldErrors.end_year)}
              placeholder="e.g. 2023"
              min={1900}
              max={new Date().getFullYear() + 10}
            />
            <FieldError
              id="emp-end-year-error"
              message={fieldErrors.end_year}
            />
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            id="emp-is-current"
            type="button"
            role="switch"
            aria-checked={fields.is_current}
            onClick={handleCurrentToggle}
            disabled={isLoading}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
              fields.is_current ? "bg-indigo-600" : "bg-gray-200"
            }`}
          >
            <span
              aria-hidden="true"
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                fields.is_current ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
          <label
            htmlFor="emp-is-current"
            className="cursor-pointer select-none text-sm font-medium text-gray-700"
          >
            I currently work here
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading && <Spinner size="h-4 w-4" color="text-white" />}
          {isLoading ? "Saving..." : "Save employment"}
        </button>
      </form>
    </section>
  );
}
