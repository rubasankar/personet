import type { PathNode } from "@/types/network";

interface PathResultProps {
  nodes: PathNode[];
  viaCloseOnly?: boolean;
}

export function PathResult({ nodes, viaCloseOnly }: PathResultProps) {
  if (nodes.length === 0) return null;

  const labels = nodes.map((node, index) => ({
    text: index === 0 ? "You" : node.name,
    key: index === 0 ? "you" : node.id,
  }));

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
      <div className="mb-3 flex items-center gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Connection path
        </h3>
        {viaCloseOnly && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
            ★ All close connections
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {labels.map(({ text, key }, index) => (
          <span key={key} className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
                index === 0
                  ? "bg-indigo-100 text-indigo-800 ring-1 ring-indigo-300"
                  : index === labels.length - 1
                    ? "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-300"
                    : "bg-gray-100 text-gray-700 ring-1 ring-gray-300"
              }`}
            >
              {text}
            </span>
            {index < labels.length - 1 && (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-4 w-4 flex-shrink-0 text-gray-400"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </span>
        ))}
      </div>

      <p className="mt-2 text-xs text-gray-500">
        {nodes.length - 1} hop{nodes.length - 1 !== 1 ? "s" : ""} away
      </p>
    </div>
  );
}
