'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

interface UseTimerProps {
  durationMinutes: number;
  onTimeUp: () => void;
  isPaused?: boolean;
}

export const useTimer = ({ durationMinutes, onTimeUp, isPaused = false }: UseTimerProps) => {
  const [timeLeft, setTimeLeft] = useState(durationMinutes * 60); // in seconds
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const pausedTimeRef = useRef<number | null>(null);

  const startTimer = useCallback(() => {
    // Defensive clearance of existing intervals to prevent acceleration
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (startTimeRef.current === null) {
      startTimeRef.current = Date.now();
    }
    pausedTimeRef.current = null;

    intervalRef.current = setInterval(() => {
      if (startTimeRef.current === null) return;

      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, durationMinutes * 60 - elapsed);

      setTimeLeft(remaining);

      if (remaining === 0) {
        onTimeUp();
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    }, 1000); // Optimized to 1000ms from 100ms
  }, [durationMinutes, onTimeUp]);

  const pauseTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    pausedTimeRef.current = Date.now();
  }, []);

  const resumeTimer = useCallback(() => {
    if (pausedTimeRef.current) {
      if (startTimeRef.current) {
        // Adjust start time to account for paused duration
        const pausedDuration = Date.now() - pausedTimeRef.current;
        startTimeRef.current += pausedDuration;
      }
      pausedTimeRef.current = null;
      startTimer();
    }
  }, [startTimer]);

  // Track the previous duration to know when to reset
  const prevDurationRef = useRef(durationMinutes);

  useEffect(() => {
    // 1. Reset logic: If duration changed, reset state first
    if (prevDurationRef.current !== durationMinutes) {
      setTimeLeft(durationMinutes * 60);
      startTimeRef.current = null;
      pausedTimeRef.current = null;
      prevDurationRef.current = durationMinutes;
    }

    // 2. Control logic: Handle Pause/Resume/Start
    if (isPaused) {
      pauseTimer();
    } else {
      if (pausedTimeRef.current) {
        resumeTimer();
      } else {
        startTimer();
      }
    }

    // 3. Cleanup: Absolute protection against leaking intervals
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPaused, durationMinutes, startTimer, pauseTimer, resumeTimer]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  const formatTime = (mins: number, secs: number): string => {
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getColor = (): string => {
    if (timeLeft <= 60) return 'text-red-600'; // < 1 min
    if (timeLeft <= 300) return 'text-yellow-600'; // < 5 min
    return 'text-green-600'; // default
  };

  const isWarning = timeLeft <= 300; // < 5 min

  return {
    timeLeft,
    formattedTime: formatTime(minutes, seconds),
    color: getColor(),
    isWarning,
    minutes,
    seconds,
  };
};
