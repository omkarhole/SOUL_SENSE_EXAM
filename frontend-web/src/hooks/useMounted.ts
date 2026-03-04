'use client';

import { useEffect, useState } from 'react';

/**
 * Hook to determine if the component has mounted on the client.
 * Essential for components that rely on window/navigator state
 * to avoid hydration mismatches between SSR and Client render.
 */
export function useMounted() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted;
}
