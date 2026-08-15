import type { SignupFieldErrors } from "@/types/profile";

/**
 * Returns Tailwind class string for a form input, varying on error state.
 */
export function fieldClass(hasError: boolean): string {
  return `mt-1 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none transition focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 ${
    hasError
      ? "border-red-400 bg-red-50 focus:ring-red-400"
      : "border-gray-300 bg-white focus:border-indigo-500"
  }`;
}

/**
 * Client-side validation for the signup form.
 */
export function validateSignupForm(
  name: string,
  email: string,
  password: string,
): SignupFieldErrors {
  const errors: SignupFieldErrors = {};

  if (name.trim().length < 1 || name.trim().length > 100) {
    errors.name = "Name must be between 1 and 100 characters.";
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    errors.email = "Please enter a valid email address.";
  }

  if (password.length < 8 || password.length > 128) {
    errors.password = "Password must be between 8 and 128 characters.";
  }

  return errors;
}
