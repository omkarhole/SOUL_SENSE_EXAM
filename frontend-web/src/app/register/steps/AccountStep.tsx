import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Eye,
  EyeOff,
  Loader2,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  ArrowRight,
  Mail,
} from 'lucide-react';
import { FormField } from '@/components/forms';
import { Button, Input } from '@/components/ui';
import { PasswordStrengthIndicator } from '@/components/auth';
import { cn } from '@/lib/utils';
import { authApi } from '@/lib/api/auth';
import { useDebounce } from '@/hooks/useDebounce';
import { StepProps } from '../registerTypes';

export default function AccountStep({
  methods,
  isLoading,
  showPassword,
  setShowPassword,
  availabilityCache,
  onNext,
  onBack,
  handleFocus,
  canProceed,
}: StepProps) {
  const [localStatus, setLocalStatus] = useState<
    'idle' | 'loading' | 'available' | 'taken' | 'invalid'
  >('idle');

  const handleContinue = async () => {
    const isValid = await methods.trigger(['username', 'email', 'password', 'confirmPassword']);
    if (isValid && localStatus !== 'taken' && localStatus !== 'loading') {
      onNext?.();
    }
  };

  const usernameValue = methods.watch('username');
  const debouncedUsername = useDebounce(usernameValue, 500);

  useEffect(() => {
    if (!debouncedUsername || debouncedUsername.length < 3) {
      setLocalStatus('idle');
      return;
    }

    const reserved = ['admin', 'root', 'support', 'soulsense', 'system', 'official'];
    if (reserved.includes(debouncedUsername.toLowerCase())) {
      setLocalStatus('taken');
      return;
    }

    if (availabilityCache?.has(debouncedUsername)) {
      setLocalStatus(availabilityCache.get(debouncedUsername)!.available ? 'available' : 'taken');
      return;
    }

    const checkAvailability = async () => {
      setLocalStatus('loading');
      try {
        const data = await authApi.checkUsernameAvailability(debouncedUsername);
        availabilityCache?.set(debouncedUsername, data);
        setLocalStatus(data.available ? 'available' : 'taken');
      } catch (error) {
        console.error('Error checking username availability:', error);
        setLocalStatus('idle');
      }
    };

    checkAvailability();
  }, [debouncedUsername, availabilityCache]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4 text-primary">
        <Mail className="w-5 h-5" />
        <h3 className="font-semibold">Account Details</h3>
      </div>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
      >
        <FormField
          control={methods.control}
          name="username"
          label="Username"
          placeholder="johndoe"
          required
          disabled={isLoading}
          onFocus={() => handleFocus('username')}
        >
          {(fieldProps) => (
            <div className="relative">
              <Input
                {...fieldProps}
                className={cn(
                  fieldProps.className,
                  localStatus === 'available' && 'border-green-500 focus-visible:ring-green-500',
                  localStatus === 'taken' && 'border-red-500 focus-visible:ring-red-500'
                )}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center">
                {localStatus === 'loading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                )}
                {localStatus === 'available' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                {localStatus === 'taken' && <XCircle className="h-4 w-4 text-red-500" />}
              </div>
              {localStatus === 'taken' && (
                <p className="text-[10px] text-red-500 mt-1 absolute -bottom-4 left-0">
                  Username taken
                </p>
              )}
              {localStatus === 'available' && (
                <p className="text-[10px] text-green-500 mt-1 absolute -bottom-4 left-0">
                  Available
                </p>
              )}
            </div>
          )}
        </FormField>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.15 }}
      >
        <FormField
          control={methods.control}
          name="email"
          label="Email"
          placeholder="you@example.com"
          type="email"
          required
          disabled={isLoading}
          onFocus={() => handleFocus('email')}
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
      >
        <FormField
          control={methods.control}
          name="password"
          label="Password"
          required
          onFocus={() => handleFocus('password')}
        >
          {(fieldProps) => (
            <div className="relative space-y-2">
              <Input
                {...fieldProps}
                type={showPassword ? 'text' : 'password'}
                disabled={isLoading}
                autoComplete="new-password"
              />
              <PasswordStrengthIndicator password={fieldProps.value || ''} />
            </div>
          )}
        </FormField>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.25 }}
      >
        <FormField
          control={methods.control}
          name="confirmPassword"
          label="Confirm Password"
          required
          onFocus={() => handleFocus('confirmPassword')}
        >
          {(fieldProps) => (
            <div className="relative">
              <Input
                {...fieldProps}
                type={showPassword ? 'text' : 'password'}
                disabled={isLoading}
                autoComplete="new-password"
              />
            </div>
          )}
        </FormField>
      </motion.div>

      <div className="flex items-center space-x-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowPassword?.(!showPassword)}
          disabled={isLoading}
          className="text-xs h-8"
        >
          {showPassword ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
          {showPassword ? 'Hide' : 'Show'} password
        </Button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex gap-3 pt-4"
      >
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={isLoading}
          className="flex-1"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button
          type="button"
          onClick={handleContinue}
          disabled={isLoading || !canProceed || localStatus === 'loading' || localStatus === 'taken'}
          className="flex-1"
        >
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </motion.div>
    </div>
  );
}