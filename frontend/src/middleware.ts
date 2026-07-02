import { NextRequest, NextResponse } from "next/server";

/**
 * UX-only gate for the admin dashboard.
 *
 * The `vc_logged_in` cookie is set/cleared alongside the JWT in lib/api.ts.
 * This middleware only prevents a flash of the dashboard shell for logged-out
 * visitors — real enforcement lives server-side (`require_admin` on every
 * /api/tickets and /api/customers route).
 */
export function middleware(request: NextRequest) {
  if (request.cookies.get("vc_logged_in")?.value === "1") {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("from", request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
