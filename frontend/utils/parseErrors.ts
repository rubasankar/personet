import type { FastAPIValidationError } from "@/types/api";

/**
 * Flattens a FastAPI 422 detail array into a plain { field: message } map.
 * The field name is taken from the last element of `loc`.
 */
export function parseValidationErrors(
  detail: FastAPIValidationError[],
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const err of detail) {
    const field = String(err.loc[err.loc.length - 1]);
    errors[field] = err.msg;
  }
  return errors;
}
