export function SkeletonCard() {
  return (
    <div
      className="animate-pulse rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-200"
      aria-hidden="true"
    >
      <div className="mb-3 h-4 w-2/5 rounded bg-gray-200" />
      <div className="mb-2 h-3 w-3/5 rounded bg-gray-200" />
      <div className="h-3 w-1/4 rounded bg-gray-200" />
    </div>
  );
}
