"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import { SuccessBanner } from "@/components/ui/SuccessBanner";
import type { FastAPIValidationError } from "@/types/api";
import type { SignupFieldErrors } from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass, validateSignupForm } from "@/utils/validation";

export default function SignupPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [fieldErrors, setFieldErrors] = useState<SignupFieldErrors>({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    setGlobalError(null);
    setSuccessMessage(null);

    const clientErrors = validateSignupForm(name, email, password);
    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors);
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email, password }),
      });

      if (res.status === 201) {
        setSuccessMessage("Account created! Redirecting to login...");
        setTimeout(() => router.push("/login"), 1500);
        return;
      }

      if (res.status === 409) {
        setFieldErrors({ email: "Email is already in use." });
        return;
      }

      if (res.status === 422) {
        const body = await res.json();
        const detail: FastAPIValidationError[] = body.detail ?? [];
        setFieldErrors(parseValidationErrors(detail) as SignupFieldErrors);
        return;
      }

      if (res.status === 503) {
        setGlobalError(
          "The service is temporarily unavailable. Please try again later.",
        );
        return;
      }

      setGlobalError("An unexpected error occurred. Please try again.");
    } catch {
      setGlobalError(
        "Unable to reach the service. Please check your connection and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-gray-200">
          <h1 className="mb-6 text-2xl font-semibold tracking-tight text-gray-900">
            Create your account
          </h1>

          {successMessage && (
            <div className="mb-5">
              <SuccessBanner message={successMessage} />
            </div>
          )}

          {globalError && (
            <div className="mb-5">
              <ErrorBanner message={globalError} />
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label
                htmlFor="name"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Name
              </label>
              <input
                id="name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading || !!successMessage}
                aria-describedby={fieldErrors.name ? "name-error" : undefined}
                aria-invalid={!!fieldErrors.name}
                className={fieldClass(!!fieldErrors.name)}
              />
              <FieldError id="name-error" message={fieldErrors.name} />
            </div>

            <div>
              <label
                htmlFor="email"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
                aria-invalid={!!fieldErrors.email}
                className={fieldClass(!!fieldErrors.email)}
              />
              <FieldError id="email-error" message={fieldErrors.email} />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                aria-describedby={
                  fieldErrors.password ? "password-error" : "password-hint"
                }
                aria-invalid={!!fieldErrors.password}
                className={fieldClass(!!fieldErrors.password)}
              />
              {fieldErrors.password ? (
                <FieldError
                  id="password-error"
                  message={fieldErrors.password}
                />
              ) : (
                <p id="password-hint" className="mt-1 text-xs text-gray-500">
                  Must be 8-128 characters.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading && <Spinner size="h-4 w-4" color="text-white" />}
              {loading ? "Creating account..." : "Sign up"}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-indigo-600 hover:underline"
            >
              Log in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
