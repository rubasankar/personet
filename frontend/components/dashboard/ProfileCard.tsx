import Link from "next/link";
import type { Profile } from "@/types/profile";

interface ProfileCardProps {
  profile: Profile;
}

export function ProfileCard({ profile }: ProfileCardProps) {
  return (
    <div className="rounded-2xl bg-white px-8 py-10 shadow-sm ring-1 ring-gray-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {profile.name}
          </h2>
          {profile.bio && (
            <p className="mt-1 text-sm text-gray-600">{profile.bio}</p>
          )}
          {profile.location && (
            <p className="mt-1 flex items-center gap-1 text-sm text-gray-500">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-4 w-4 flex-shrink-0"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M9.69 18.933l.003.001C9.89 19.02 10 19 10 19s.11.02.308-.066l.002-.001.006-.003.018-.008a5.741 5.741 0 00.281-.14c.186-.096.446-.24.757-.433.62-.384 1.445-.966 2.274-1.765C15.302 15.012 17 12.069 17 8A7 7 0 103 8c0 4.068 1.698 7.012 3.354 8.585.83.799 1.654 1.38 2.274 1.765.311.193.571.337.757.433a5.741 5.741 0 00.281.14l.018.008.006.003zM10 11a3 3 0 100-6 3 3 0 000 6z"
                  clipRule="evenodd"
                />
              </svg>
              {profile.location}
            </p>
          )}
        </div>

        <span className="inline-flex flex-shrink-0 items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700 ring-1 ring-indigo-200">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path d="M7 8a3 3 0 100-6 3 3 0 000 6zM14.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM1.615 16.428a1.224 1.224 0 01-.569-1.175 6.002 6.002 0 0111.908 0c.058.467-.172.92-.57 1.174A9.953 9.953 0 017 17a9.953 9.953 0 01-5.385-1.572zM14.5 16h-.106c.07-.297.088-.611.048-.933a7.47 7.47 0 00-1.588-3.755 4.502 4.502 0 015.874 2.636.818.818 0 01-.36.98A7.465 7.465 0 0114.5 16z" />
          </svg>
          <span>
            {profile.connection_count}{" "}
            {profile.connection_count === 1 ? "connection" : "connections"}
          </span>
        </span>
      </div>

      <div className="mt-4">
        <Link
          href="/profile/me"
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500 hover:underline"
        >
          Edit profile
        </Link>
      </div>
    </div>
  );
}
