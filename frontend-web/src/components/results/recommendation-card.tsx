import React, { useId, useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Brain,
  Target,
  Users,
  Heart,
  Lightbulb,
  HandHeart,
  MessageCircle,
  Repeat,
  Zap,
  ChevronDown,
  LucideIcon,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Recommendation } from '@/types/results';

interface RecommendationCardProps {
  recommendation: Recommendation;
  isExpanded?: boolean;
  onToggle?: () => void;
  className?: string;
  showAnimation?: boolean;
  disabled?: boolean;
}

// Category icon mapping for visual recognition
const categoryIcons: Record<string, LucideIcon> = {
  'Self-Awareness': Brain,
  'Self-Management': Target,
  'Social Awareness': Users,
  'Relationship Management': Heart,
  'Decision Making': Lightbulb,
  Empathy: HandHeart,
  Communication: MessageCircle,
  Adaptability: Repeat,
  default: Zap,
};

// Get icon component for a category (with fallback)
const getCategoryIcon = (categoryName: string): LucideIcon => {
  return categoryIcons[categoryName] || categoryIcons.default;
};

// Priority badge color schemes
const priorityStyles = {
  high: {
    bg: 'bg-rose-100 dark:bg-rose-950',
    text: 'text-rose-700 dark:text-rose-400',
    border: 'border-rose-200 dark:border-rose-900',
  },
  medium: {
    bg: 'bg-amber-100 dark:bg-amber-950',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-900',
  },
  low: {
    bg: 'bg-blue-100 dark:bg-blue-950',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-900',
  },
};

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  isExpanded: controlledExpanded,
  onToggle,
  className,
  showAnimation = true,
  disabled = false,
}) => {
  // Support both controlled and uncontrolled state
  const scopeId = useId();
  const headingId = `${scopeId}-heading`;
  const contentId = `${scopeId}-content`;
  const [internalExpanded, setInternalExpanded] = useState(false);
  const isControlled = controlledExpanded !== undefined && onToggle !== undefined;
  const isExpanded = isControlled ? controlledExpanded : internalExpanded;

  // Safe defaults for edge cases
  const safePriority = recommendation.priority || 'medium';
  const safeMessage = recommendation.message || 'No recommendation available';
  const safeCategoryName = recommendation.category_name || 'General';

  const Icon = getCategoryIcon(safeCategoryName);
  const priorityStyle = priorityStyles[safePriority];

  // Truncation logic
  const TRUNCATE_LENGTH = 100;
  const shouldTruncate = safeMessage.length > TRUNCATE_LENGTH;
  const displayMessage =
    isExpanded || !shouldTruncate ? safeMessage : `${safeMessage.substring(0, TRUNCATE_LENGTH)}...`;

  // Handle toggle
  const handleToggle = () => {
    if (disabled) return;

    if (isControlled) {
      onToggle?.();
    } else {
      setInternalExpanded(!internalExpanded);
    }
  };

  // Keyboard handler for accessibility
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  // Animation variants
  const cardVariants = showAnimation
    ? {
        initial: { opacity: 0, scale: 0.95 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.95 },
      }
    : {};

  const contentVariants = {
    collapsed: { opacity: 0, height: 0 },
    expanded: { opacity: 1, height: 'auto' },
  };

  return (
    <motion.div
      {...(showAnimation ? cardVariants : {})}
      initial={showAnimation ? 'initial' : false}
      animate={showAnimation ? 'animate' : false}
      transition={{ duration: 0.3 }}
      whileHover={!disabled && showAnimation ? { y: -2 } : {}}
    >
      <Card
        className={cn(
          'transition-all duration-200 shadow-md hover:shadow-lg',
          'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800',
          disabled && 'opacity-60 cursor-not-allowed',
          className
        )}
        variant="elevated"
      >
        {/* Header Section */}
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            {/* Icon + Title */}
            <div className="flex items-start gap-3 flex-1 min-w-0">
              {/* Category Icon */}
              <div
                className={cn(
                  'p-2 rounded-lg shrink-0',
                  'bg-slate-100 dark:bg-slate-800',
                  'text-slate-700 dark:text-slate-300'
                )}
                aria-hidden="true"
              >
                <Icon className="h-5 w-5" />
              </div>

              {/* Title */}
              <div className="flex-1 min-w-0">
                <h3
                  id={headingId}
                  className="font-bold text-base text-slate-900 dark:text-white leading-tight"
                >
                  {safeCategoryName}
                </h3>
              </div>
            </div>

            {/* Priority Badge + Expand Button */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Priority Badge (only for high priority) */}
              {safePriority === 'high' && (
                <span
                  className={cn(
                    'px-2 py-1 text-xs font-semibold rounded-full border',
                    priorityStyle.bg,
                    priorityStyle.text,
                    priorityStyle.border
                  )}
                  aria-label={`Priority: ${safePriority}`}
                >
                  High Priority
                </span>
              )}

              {/* Expand/Collapse Button */}
              {shouldTruncate && (
                <button
                  onClick={handleToggle}
                  onKeyDown={handleKeyDown}
                  disabled={disabled}
                  aria-expanded={isExpanded}
                  aria-label={isExpanded ? 'Collapse recommendation' : 'Expand recommendation'}
                  aria-controls={contentId}
                  className={cn(
                    'p-1.5 rounded-lg transition-all',
                    'hover:bg-slate-100 dark:hover:bg-slate-800',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
                    'text-slate-600 dark:text-slate-400',
                    disabled && 'cursor-not-allowed'
                  )}
                >
                  <ChevronDown
                    className={cn(
                      'h-5 w-5 transition-transform duration-200',
                      isExpanded && 'rotate-180'
                    )}
                  />
                </button>
              )}
            </div>
          </div>
        </CardHeader>

        {/* Content Section */}
        <CardContent className="pt-0">
          {/* Description */}
          <div
            id={contentId}
            role="region"
            aria-labelledby={headingId}
            className={cn(
              'text-sm text-slate-600 dark:text-slate-300 leading-relaxed',
              isExpanded && safeMessage.length > 500 && 'max-h-96 overflow-y-auto pr-2'
            )}
          >
            {/* Truncated or Full Text */}
            <p className="mb-3">{displayMessage}</p>

            {/* "See more" / "See less" text link (alternative to button) */}
            {shouldTruncate && (
              <button
                onClick={handleToggle}
                disabled={disabled}
                className={cn(
                  'text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:rounded',
                  disabled && 'cursor-not-allowed'
                )}
                aria-label={isExpanded ? 'See less' : 'See more'}
              >
                {isExpanded ? 'See less' : 'See more'}
              </button>
            )}
          </div>

          {/* Category Tag */}
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Category:
            </span>
            <span
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold',
                'bg-slate-100 dark:bg-slate-800',
                'text-slate-700 dark:text-slate-300',
                'border border-slate-200 dark:border-slate-700'
              )}
            >
              <Icon className="h-3 w-3" aria-hidden="true" />
              {safeCategoryName}
            </span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

// Respect prefers-reduced-motion
if (typeof window !== 'undefined') {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) {
    RecommendationCard.defaultProps = {
      ...RecommendationCard.defaultProps,
      showAnimation: false,
    };
  }
}

export default RecommendationCard;
