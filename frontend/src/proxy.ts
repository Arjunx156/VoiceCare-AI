import { NextRequest, NextResponse } from "next/server";

// Protect all /dashboard routes — redirect to /login if auth cookie is absent
export function proxy(request: NextRequest) {
  const isLoggedIn = request.cookies.get("vc_logged_in")?.value === "1";
  if (!isLoggedIn) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
