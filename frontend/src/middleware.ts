import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Guard all /dashboard routes — redirect to /login if the auth cookie is absent
  if (pathname.startsWith("/dashboard")) {
    const isLoggedIn = request.cookies.get("vc_logged_in")?.value === "1";
    if (!isLoggedIn) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("from", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Logged-in users visiting /login go straight to dashboard
  if (pathname === "/login") {
    const isLoggedIn = request.cookies.get("vc_logged_in")?.value === "1";
    if (isLoggedIn) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
