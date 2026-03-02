'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { profileApi } from '@/lib/api/profile';
import { usePathname, useRouter } from 'next/navigation';

export interface UseOnboardingGuardReturn {
  /** Whether the user needs to complete onboarding */
  needsOnboarding: boolean;
  /** Whether we're still checking the onboarding status */
  isChecking: boolean;
  /** Function to mark onboarding as complete locally */
  markComplete: () => void;
  /** Function to skip onboarding (for this session only) */
  skipForSession: () => void;
}

/**
 * Hook to guard routes and intercept users who haven't completed onboarding.
 * 
 * This hook checks if the current user has completed onboarding and returns
 * a flag indicating whether they should be shown the onboarding wizard.
 * 
 * @example
 * ```tsx
 * function AppLayout({ children }) {
 *   const { needsOnboarding, isChecking } = useOnboardingGuard();
 *   
 *   if (isChecking) return <LoadingScreen />;
 *   
 *   return (
 *     <>
 *       <OnboardingModal isOpen={needsOnboarding} onComplete={markComplete} />
 *       {children}
 *     </>
 *   );
 * }
 * ```
 */
export function useOnboardingGuard(): UseOnboardingGuardReturn {
  const router = useRouter();
  const pathname = usePathname();
  const [skipped, setSkipped] = useState(false);
  
  // Query for onboarding status
  const { 
    data, 
    isLoading,
    isFetching,
  } = useQuery({
    queryKey: ['onboarding', 'status'],
    queryFn: () => profileApi.getOnboardingStatus(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    refetchOnWindowFocus: false,
  });
  
  // Also check the user profile for onboarding status (as a fallback/source of truth)
  const {
    data: profileData,
    isLoading: isProfileLoading,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: () => profileApi.getUserProfile(),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
  
  // Determine if onboarding is needed
  // Priority: API status > Profile data > Default false
  const apiCompleted = data?.onboarding_completed ?? false;
  const profileCompleted = profileData?.onboarding_completed ?? false;
  const isCompleted = apiCompleted || profileCompleted;
  
  const needsOnboarding = !isCompleted && !skipped;
  const isChecking = isLoading || isProfileLoading || isFetching;
  
  // Mark onboarding as complete locally (after API call succeeds)
  const markComplete = () => {
    // The actual state update comes from the query invalidation
    // This is just a trigger for any local UI updates if needed
  };
  
  // Skip onboarding for this session only
  const skipForSession = () => {
    setSkipped(true);
  };
  
  return {
    needsOnboarding,
    isChecking,
    markComplete,
    skipForSession,
  };
}
