'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Question } from '@/lib/api/questions';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui';
import { cn } from '@/lib/utils';

interface QuestionCardProps {
  question: Question;
  selectedValue?: number;
  onSelect: (value: number) => void;
  disabled?: boolean;
  totalQuestions?: number;
  currentIndex?: number;
}

const LIKERT_LABELS: Record<number, string> = {
  1: 'Strongly Disagree',
  2: 'Disagree',
  3: 'Neutral',
  4: 'Agree',
  5: 'Strongly Agree',
};

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  selectedValue,
  onSelect,
  disabled = false,
  totalQuestions,
  currentIndex,
}) => {
  const optionsRef = useRef<(HTMLButtonElement | null)[]>([]);

  // Default to 1-5 scale if question.options is missing or empty
  const options = question.options?.length
    ? question.options
    : [1, 2, 3, 4, 5].map((v) => ({ value: v, label: LIKERT_LABELS[v] }));

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (disabled) return;

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      const nextIndex = (index + 1) % options.length;
      optionsRef.current[nextIndex]?.focus();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      const prevIndex = (index - 1 + options.length) % options.length;
      optionsRef.current[prevIndex]?.focus();
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(options[index].value);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="w-full max-w-2xl mx-auto"
    >
      <Card className="overflow-hidden border-none shadow-xl bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
              {question.category || 'General'}
            </span>
          </div>
          {totalQuestions !== undefined && currentIndex !== undefined && (
            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Question {currentIndex + 1} of {totalQuestions}
            </span>
          )}
        </CardHeader>

        <CardContent className="pt-6 pb-8">
          <h2
            id={`question-${question.id}`}
            className="text-2xl md:text-3xl font-bold text-slate-800 dark:text-slate-100 leading-tight"
          >
            {question.text}
          </h2>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4 pt-4 pb-8">
          <div
            role="radiogroup"
            aria-labelledby={`question-${question.id}`}
            className="grid grid-cols-1 sm:grid-cols-5 gap-3 w-full"
          >
            {options.map((option, idx) => {
              const isSelected = selectedValue === option.value;

              return (
                <button
                  key={option.value}
                  ref={(el: HTMLButtonElement | null) => {
                    optionsRef.current[idx] = el;
                  }}
                  role="radio"
                  aria-checked={isSelected}
                  disabled={disabled}
                  onClick={() => onSelect(option.value)}
                  onKeyDown={(e) => handleKeyDown(e, idx)}
                  tabIndex={isSelected || (selectedValue === undefined && idx === 0) ? 0 : -1}
                  className={cn(
                    'relative flex flex-col items-center justify-center p-4 rounded-xl transition-all duration-200 border-2 text-center group',
                    'hover:scale-105 active:scale-95',
                    isSelected
                      ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-indigo-400 dark:hover:border-indigo-500',
                    disabled && 'opacity-50 cursor-not-allowed hover:scale-100'
                  )}
                >
                  <span
                    className={cn(
                      'text-xl font-bold mb-1',
                      isSelected ? 'text-white' : 'text-slate-900 dark:text-white'
                    )}
                  >
                    {option.value}
                  </span>
                  <span className="text-[10px] uppercase tracking-wider font-semibold opacity-80 line-clamp-1">
                    {option.label}
                  </span>

                  {isSelected && (
                    <motion.div
                      layoutId={`question-active-bg-${question.id}`}
                      className="absolute inset-0 rounded-xl bg-indigo-600 -z-10"
                      transition={{ type: 'tween', ease: 'easeOut', duration: 0.4 }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
};
