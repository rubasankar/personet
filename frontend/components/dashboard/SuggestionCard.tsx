import type { Suggestion } from "@/types/network";

interface SuggestionCardProps {
  suggestion: Suggestion;
}

export function SuggestionCard({ suggestion }: SuggestionCardProps) {
  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200">
      <h3 className="text-sm font-semibold text-gray-900">{suggestion.name}</h3>

      {suggestion.shared_context.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {suggestion.shared_context.map((ctx) => (
            <span
              key={ctx}
              className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-indigo-200"
            >
              {ctx}
            </span>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-1.5">
        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
          {suggestion.overlap_score}{" "}
          {suggestion.overlap_score === 1 ? "overlap" : "overlaps"}
        </span>
      </div>
    </div>
  );
}
