"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { FieldError } from "@/components/ui/FieldError";
import { Spinner } from "@/components/ui/Spinner";
import type { FastAPIValidationError } from "@/types/api";
import type { LoginFieldErrors } from "@/types/profile";
import { parseValidationErrors } from "@/utils/parseErrors";
import { fieldClass } from "@/utils/validation";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [generalError, setGeneralError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  function clearErrors() {
    setFieldErrors({});
    setGeneralError("");
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    clearErrors();
    setIsLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        router.push("/dashboard");
        return;
      }

      if (res.status === 401) {
        setGeneralError(
          "Invalid credentials. Please check your email and password.",
        );
        return;
      }

      if (res.status === 422) {
        const data = await res.json();
        const detail: FastAPIValidationError[] = data.detail ?? [];
        const errors = parseValidationErrors(detail) as LoginFieldErrors;
        if (Object.keys(errors).length === 0) {
          setGeneralError(
            "Please correct the highlighted fields and try again.",
          );
        } else {
          setFieldErrors(errors);
        }
        return;
      }

      if (res.status === 503) {
        setGeneralError(
          "The service is temporarily unavailable. Please try again later.",
        );
        return;
      }

      setGeneralError("An unexpected error occurred. Please try again.");
    } catch {
      setGeneralError(
        "Unable to reach the server. Please check your connection and try again.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Sign in to your account
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-indigo-600 underline underline-offset-2 hover:text-indigo-500"
            >
              Create one
            </Link>
          </p>
        </div>

        <div className="rounded-2xl bg-white px-8 py-10 shadow-sm ring-1 ring-gray-200">
          {generalError && (
            <div className="mb-6">
              <ErrorBanner message={generalError} />
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
                aria-invalid={!!fieldErrors.email}
                className={fieldClass(!!fieldErrors.email)}
                placeholder="you@example.com"
              />
              <FieldError id="email-error" message={fieldErrors.email} />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-describedby={
                  fieldErrors.password ? "password-error" : undefined
                }
                aria-invalid={!!fieldErrors.password}
                className={fieldClass(!!fieldErrors.password)}
                placeholder="********"
              />
              <FieldError id="password-error" message={fieldErrors.password} />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? (
                <>
                  <Spinner size="h-4 w-4" color="text-white" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
