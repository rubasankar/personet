import { type NextRequest, NextResponse } from "next/server";

const PROTECTED = ["/dashboard", "/profile", "/people", "/connections"];

export function proxy(req: NextRequest) {
  const token = req.cookies.get("access_token");
  const isProtected = PROTECTED.some((p) => req.nextUrl.pathname.startsWith(p));
  if (isProtected && !token) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/profile/:path*",
    "/people/:path*",
    "/connections/:path*",
  ],
};
