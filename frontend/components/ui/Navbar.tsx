"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Spinner } from "@/components/ui/Spinner";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/people", label: "People" },
  { href: "/connections", label: "Connections" },
  { href: "/profile/me", label: "Profile" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      // Clear the httpOnly cookie by hitting an endpoint that sets it expired,
      // or just navigate - the proxy will reject subsequent protected requests.
      // We call the logout endpoint if one exists, otherwise just clear client state.
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Best-effort; even if it fails, redirect to login
    } finally {
      router.push("/login");
    }
  }

  return (
    <nav
      className="border-b border-gray-200 bg-white"
      aria-label="Main navigation"
    >
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link
          href="/dashboard"
          className="text-base font-bold text-indigo-600 tracking-tight"
        >
          PerNet
        </Link>

        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                pathname === href || pathname.startsWith(`${href}/`)
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              {label}
            </Link>
          ))}

          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="ml-2 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 transition hover:bg-red-50 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:opacity-50"
          >
            {loggingOut ? (
              <Spinner size="h-3.5 w-3.5" color="text-red-500" />
            ) : null}
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
