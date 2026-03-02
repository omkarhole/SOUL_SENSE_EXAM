// Export all results components
// Note: Heavy components using recharts/framer-motion/jspdf are dynamically imported
// from @/lib/dynamic-imports to prevent bloating the initial bundle.

// Lightweight components - safe to export statically
export { default as RecommendationCard } from './recommendation-card';
export { default as CategoryBreakdown } from './category-breakdown';

// Export type for ExamResult
export type { ExamResult } from './history-chart';

// ⚠️ Heavy components are NOT exported here to avoid eager loading:
// - HistoryChart (uses recharts)
// - ScoreGauge (uses framer-motion)
// - export-pdf (uses jspdf, html2canvas)
// Use dynamic imports instead:
//   import { HistoryChart, ScoreGauge, ExportPDF } from '@/lib/dynamic-imports';
