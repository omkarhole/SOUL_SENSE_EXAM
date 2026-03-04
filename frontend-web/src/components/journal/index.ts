// Export all journal components
// Note: Heavy chart components using recharts are dynamically imported
// from @/lib/dynamic-imports to prevent bloating the initial bundle.

export { JournalEntryCard } from './entry-card';
export { default as JournalEditor } from './journal-editor';
export { MoodSlider } from './mood-slider';
export { TagSelector } from './tag-selector';
export { JournalListContainer } from './journal-list';

// ⚠️ MoodTrend is NOT exported here to avoid eager loading recharts
// Use dynamic import instead:
//   import { MoodTrend } from '@/lib/dynamic-imports';
