import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-2xl text-center">
        {/* Logo / wordmark */}
        <div className="mb-6 inline-flex items-center justify-center rounded-2xl bg-indigo-600 p-4 shadow-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="h-10 w-10 text-white"
            aria-hidden="true"
          >
            <path d="M4.5 6.375a4.125 4.125 0 118.25 0 4.125 4.125 0 01-8.25 0zM14.25 8.625a3.375 3.375 0 116.75 0 3.375 3.375 0 01-6.75 0zM1.5 19.125a7.125 7.125 0 0114.212-1.017A3.375 3.375 0 0117.625 21H3.375A1.875 1.875 0 011.5 19.125zM17.625 21a3.375 3.375 0 01-3.375-3.375c0-.275.033-.543.096-.8A5.625 5.625 0 0122.5 19.125a1.875 1.875 0 01-1.875 1.875h-3z" />
          </svg>
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          PerNet
        </h1>
        <p className="mt-4 text-lg text-gray-600">
          Explore your professional network through graph-powered connections.
          Discover who you know, how you&apos;re connected, and who you should
          meet.
        </p>

        {/* Feature highlights */}
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white px-5 py-6 shadow-sm ring-1 ring-gray-200">
            <div className="mb-3 inline-flex items-center justify-center rounded-xl bg-indigo-50 p-2.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-5 w-5 text-indigo-600"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-sm font-semibold text-gray-900">
              Connection paths
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Find the shortest path between you and anyone in the network.
            </p>
          </div>

          <div className="rounded-2xl bg-white px-5 py-6 shadow-sm ring-1 ring-gray-200">
            <div className="mb-3 inline-flex items-center justify-center rounded-xl bg-indigo-50 p-2.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-5 w-5 text-indigo-600"
                aria-hidden="true"
              >
                <path d="M7 8a3 3 0 100-6 3 3 0 000 6zM14.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM1.615 16.428a1.224 1.224 0 01-.569-1.175 6.002 6.002 0 0111.908 0c.058.467-.172.92-.57 1.174A9.953 9.953 0 017 17a9.953 9.953 0 01-5.385-1.572zM14.5 16h-.106c.07-.297.088-.611.048-.933a7.47 7.47 0 00-1.588-3.755 4.502 4.502 0 015.874 2.636.818.818 0 01-.36.98A7.465 7.465 0 0114.5 16z" />
              </svg>
            </div>
            <h2 className="text-sm font-semibold text-gray-900">
              Smart suggestions
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Get people-you-may-know suggestions based on shared context.
            </p>
          </div>

          <div className="rounded-2xl bg-white px-5 py-6 shadow-sm ring-1 ring-gray-200">
            <div className="mb-3 inline-flex items-center justify-center rounded-xl bg-indigo-50 p-2.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-5 w-5 text-indigo-600"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-sm font-semibold text-gray-900">
              Company search
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Find everyone in your network who works at a given company.
            </p>
          </div>
        </div>

        {/* CTA buttons */}
        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Link
            href="/signup"
            className="w-full rounded-xl bg-indigo-600 px-8 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 sm:w-auto"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="w-full rounded-xl bg-white px-8 py-3 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-gray-300 transition hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
          >
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
