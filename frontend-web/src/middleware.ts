import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware to handle global request/response logic.
 * Implements route protection for authenticated routes.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Define protected routes
  const protectedPrefixes = ['/app', '/admin'];

  // Define auth routes
  const authRoutes = ['/login', '/register', '/forgot-password'];

  // Read authentication token from cookies
  const token = request.cookies.get('refresh_token')?.value;

  // Check if current path is protected
  const isProtected = protectedPrefixes.some((prefix) => pathname.startsWith(prefix));

  // Check if current path is an auth route
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));

  if (isProtected && !token) {
    // Redirect unauthenticated users to login
    const loginUrl = new URL('/login', request.url);
    // Preserve the original URL as callback
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthRoute && token) {
    // Redirect authenticated users away from auth pages to dashboard
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
