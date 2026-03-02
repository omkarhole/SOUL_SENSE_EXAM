/**
 * Dynamic imports for heavy components to enable code splitting and lazy loading.
 * This reduces initial bundle size and improves Time to Interactive (TTI).
 * 
 * Usage:
 *   import { DashboardCharts } from '@/lib/dynamic-imports';
 * 
 * These components are loaded on-demand when rendered, not at page load.
 */

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';
import React from 'react';

// ============================================================================
// DASHBOARD CHART COMPONENTS (recharts - ~70KB gzipped)
// ============================================================================

/**
 * Dashboard Charts with recharts - heavy visualization library
 * Only loaded when user navigates to dashboard
 */
export const DashboardCharts = dynamic(
  () => import('@/components/dashboard/dashboard-charts'),
  {
    loading: () => (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

/**
 * Activity Area Chart - recharts based
 */
export const ActivityAreaChart = dynamic(
  () => import('@/components/dashboard/charts/activity-area-chart').then(mod => ({ default: mod.ActivityAreaChart })),
  {
    loading: () => (
      <div className="h-[250px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

/**
 * Contribution Mix Chart - recharts based
 */
export const ContributionMix = dynamic(
  () => import('@/components/dashboard/charts/contribution-mix').then(mod => ({ default: mod.ContributionMixChart })),
  {
    loading: () => (
      <div className="h-[200px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

/**
 * Repository Sunburst Chart - recharts based
 */
export const RepositorySunburst = dynamic(
  () => import('@/components/dashboard/charts/repository-sunburst').then(mod => ({ default: mod.RepositorySunburst })),
  {
    loading: () => (
      <div className="h-[300px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

// ============================================================================
// FORCE GRAPH COMPONENTS (react-force-graph-2d + d3-force - ~150KB gzipped)
// ============================================================================

/**
 * Force Directed Graph - heavy D3-based visualization
 * Requires browser canvas APIs
 */
export const ForceDirectedGraph = dynamic(
  () => import('@/components/dashboard/charts/force-directed-graph').then(mod => ({ default: mod.ForceDirectedGraph })),
  {
    loading: () => (
      <div className="h-[400px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
        <span className="text-slate-400 text-sm">Loading visualization...</span>
      </div>
    ),
    ssr: false, // Force graph requires browser canvas APIs
  }
) as ComponentType<any>;

// ============================================================================
// RESULTS COMPONENTS (recharts)
// ============================================================================

/**
 * History Chart - recharts based results history
 */
export const HistoryChart = dynamic(
  () => import('@/components/results/history-chart'),
  {
    loading: () => (
      <div className="h-[400px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

/**
 * Score Gauge - framer-motion based
 */
export const ScoreGauge = dynamic(
  () => import('@/components/results/score-gauge'),
  {
    loading: () => (
      <div className="h-[180px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Uses framer-motion animations
  }
) as ComponentType<any>;

// ============================================================================
// PDF EXPORT COMPONENTS (jspdf + html2canvas - ~180KB gzipped)
// ============================================================================

/**
 * Export PDF - heavy libraries (jspdf, html2canvas)
 * Only loaded when user clicks export button
 */
export const ExportPDF = dynamic(
  () => import('@/components/results/export-pdf').then(mod => ({ default: mod.ExportPDF })),
  {
    loading: () => (
      <button disabled className="opacity-50 cursor-not-allowed">
        Loading...
      </button>
    ),
    ssr: false, // PDF generation requires browser APIs
  }
) as ComponentType<any>;

// ============================================================================
// JOURNAL COMPONENTS (recharts)
// ============================================================================

/**
 * Mood Trend Chart - recharts based
 */
export const MoodTrend = dynamic(
  () => import('@/components/journal/mood-trend').then(mod => ({ default: mod.MoodTrend })),
  {
    loading: () => (
      <div className="h-[200px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false, // Recharts requires browser APIs
  }
) as ComponentType<any>;

// ============================================================================
// ONBOARDING COMPONENTS (framer-motion - ~40KB gzipped)
// ============================================================================

/**
 * Onboarding Modal - framer-motion animations
 * Lazy loaded since it's not needed for returning users
 */
export const OnboardingModal = dynamic(
  () => import('@/components/onboarding/OnboardingModal').then(mod => ({ default: mod.OnboardingModal })),
  {
    loading: () => null, // Modal starts closed, no need for loading state
    ssr: false,
  }
) as ComponentType<any>;

/**
 * Onboarding Wizard - framer-motion animations
 */
export const OnboardingWizard = dynamic(
  () => import('@/components/onboarding/OnboardingWizard').then(mod => ({ default: mod.OnboardingWizard })),
  {
    loading: () => (
      <div className="h-[400px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false,
  }
) as ComponentType<any>;

// ============================================================================
// GAMIFICATION COMPONENTS (framer-motion)
// ============================================================================

/**
 * Achievement Gallery - framer-motion animations
 */
export const AchievementGallery = dynamic(
  () => import('@/components/gamification/achievement-gallery').then(mod => ({ default: mod.AchievementGallery })),
  {
    loading: () => (
      <div className="h-[300px] w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" />
    ),
    ssr: false,
  }
) as ComponentType<any>;
