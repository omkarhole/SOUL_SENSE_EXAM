'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useMounted } from '@/hooks/useMounted';

// Use dynamic import with ssr: false to prevent hydration mismatch
// on the floating navbar which depends on complex client-side state
const FloatingNavbar = dynamic(
  () => import('./floating-navbar').then((mod) => mod.FloatingNavbar),
  { ssr: false }
);

/**
 * Conditionally renders the floating navbar based on pathname.
 * We hide it on authentication-related pages to prevent visual overlap
 * and redundant "Sign In" CTA on the login/register flows.
 */
export function NavbarController() {
  const pathname = usePathname();

  const isMounted = useMounted();

  const hideOnRoutes = new Set(['/forgot-password']);
  if (!isMounted || hideOnRoutes.has(pathname)) {
    return null;
  }

  return <FloatingNavbar />;
}
