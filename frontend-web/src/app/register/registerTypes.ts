import { z } from 'zod';
import { registrationSchema } from '@/lib/validation';
import { UseFormReturn } from 'react-hook-form';

export type RegisterFormData = z.infer<typeof registrationSchema>;

export interface StepContentProps {
  methods: UseFormReturn<RegisterFormData>;
  isLoading: boolean;
  onNext?: () => void;
  onBack?: () => void;
  canProceed: boolean;
  handleFocus: (fieldName: string) => void;
}

export interface StepProps extends StepContentProps {
  showPassword?: boolean;
  setShowPassword?: (show: boolean) => void;
  availabilityCache?: Map<string, { available: boolean; message: string }>;
}