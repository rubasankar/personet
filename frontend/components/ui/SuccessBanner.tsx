interface SuccessBannerProps {
  message: string;
}

export function SuccessBanner({ message }: SuccessBannerProps) {
  return (
    <output
      aria-live="polite"
      className="block rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700 ring-1 ring-green-200"
    >
      {message}
    </output>
  );
}
