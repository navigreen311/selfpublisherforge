import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Middleware for Authentication Route Guards
 *
 * Intercepts requests to protected dashboard routes and redirects
 * unauthenticated users to the login page before the page renders,
 * preventing the flash of dashboard skeleton UI.
 *
 * Authentication check: Looks for an "access_token" cookie.
 *
 * NOTE: The app currently stores tokens in localStorage (see lib/api.ts
 * and lib/store.ts). Since middleware runs on the server/edge and cannot
 * access localStorage, the login flow should also set an "access_token"
 * cookie (even a simple boolean flag cookie like "authenticated=true")
 * so this middleware can gate access. Until that cookie is set during
 * login, this middleware will redirect all dashboard access to /login.
 *
 * To enable this fully, update the setTokens function in lib/store.ts
 * to also set: document.cookie = `access_token=${accessToken}; path=/; SameSite=Lax`;
 */

// Routes that do NOT require authentication
const PUBLIC_PATHS = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/oauth",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths, static assets, API routes, and Next.js internals
  if (
    isPublicPath(pathname) ||
    pathname === "/" ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon")
  ) {
    return NextResponse.next();
  }

  // Check for auth token in cookies
  const token =
    request.cookies.get("access_token")?.value ||
    request.cookies.get("token")?.value;

  if (!token) {
    // Build the login URL with a returnTo parameter so we can redirect
    // back after successful login
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("returnTo", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

/**
 * Matcher configuration: only run middleware on dashboard-related routes.
 * This avoids unnecessary middleware execution on static files, images,
 * API routes, and public pages.
 *
 * The matcher covers all routes under the (dashboard) route group:
 * /dashboard, /projects, /writing, /advertising, /marketing, /publishing,
 * /analytics, /settings, /knowledge, /pipeline, /product-page, /agents,
 * /onboarding, /market, and any sub-paths thereof.
 */
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/projects/:path*",
    "/writing/:path*",
    "/advertising/:path*",
    "/marketing/:path*",
    "/publishing/:path*",
    "/analytics/:path*",
    "/settings/:path*",
    "/knowledge/:path*",
    "/pipeline/:path*",
    "/product-page/:path*",
    "/agents/:path*",
    "/onboarding/:path*",
    "/market/:path*",
  ],
};
