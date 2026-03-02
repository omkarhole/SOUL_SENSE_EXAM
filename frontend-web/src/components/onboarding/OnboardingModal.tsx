'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { OnboardingWizard } from './OnboardingWizard';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface OnboardingModalProps {
  isOpen: boolean;
  onComplete: () => void;
  onSkip?: () => void;
  preventClose?: boolean;
}

export function OnboardingModal({ 
  isOpen, 
  onComplete, 
  onSkip,
  preventClose = true 
}: OnboardingModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Full-screen backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-sm"
          />

          {/* Modal container */}
          <div className="fixed inset-0 z-[101] overflow-y-auto">
            <div className="min-h-full flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8">
              {/* Logo/Brand */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="mb-8 text-center"
              >
                <div className="inline-flex items-center gap-2">
                  <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
                    <span className="text-primary-foreground font-bold text-lg">S</span>
                  </div>
                  <span className="text-xl font-bold text-foreground">SoulSense</span>
                </div>
              </motion.div>

              {/* Onboarding Content */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: 0.1, duration: 0.3 }}
                className="w-full max-w-3xl"
              >
                <OnboardingWizard
                  onComplete={onComplete}
                  onSkip={!preventClose ? onSkip : undefined}
                />
              </motion.div>

              {/* Footer text */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="mt-8 text-sm text-muted-foreground text-center max-w-md"
              >
                Your responses help us personalize your experience. 
                You can update these preferences anytime in your settings.
              </motion.p>
            </div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
