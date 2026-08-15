interface SpinnerProps {
  /** Tailwind size classes, e.g. "h-4 w-4". Defaults to "h-5 w-5". */
  size?: string;
  /** Tailwind color class. Defaults to "text-indigo-500". */
  color?: string;
}

export function Spinner({
  size = "h-5 w-5",
  color = "text-indigo-500",
}: SpinnerProps) {
  return (
    <svg
      className={`animate-spin ${size} ${color}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
