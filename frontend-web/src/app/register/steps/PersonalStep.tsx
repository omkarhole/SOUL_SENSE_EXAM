import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { FormField } from '@/components/forms';
import { Button } from '@/components/ui';
import { User } from 'lucide-react';
import { StepProps } from '../registerTypes';

export default function PersonalStep({ methods, isLoading, onNext, handleFocus, canProceed }: StepProps) {
  const handleContinue = async () => {
    const isValid = await methods.trigger(['firstName', 'age', 'gender']);
    if (isValid) {
      onNext?.();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4 text-primary">
        <User className="w-5 h-5" />
        <h3 className="font-semibold">Personal Information</h3>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <FormField
            control={methods.control}
            name="firstName"
            label="First name"
            placeholder="John"
            required
            disabled={isLoading}
            onFocus={() => handleFocus('firstName')}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 }}
        >
          <FormField
            control={methods.control}
            name="lastName"
            label="Last name"
            placeholder="Doe"
            disabled={isLoading}
            onFocus={() => handleFocus('lastName')}
          />
        </motion.div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <FormField
            control={methods.control}
            name="age"
            label="Age"
            placeholder="25"
            type="number"
            required
            disabled={isLoading}
            onFocus={() => handleFocus('age')}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25 }}
        >
          <FormField
            control={methods.control}
            name="gender"
            label="Gender"
            required
            onFocus={() => handleFocus('gender')}
          >
            {(fieldProps) => (
              <select
                {...fieldProps}
                disabled={isLoading}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
                onChange={(e) => {
                  fieldProps.onChange(e);
                  handleFocus('gender');
                }}
              >
                <option value="">Select gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            )}
          </FormField>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="pt-4"
      >
        <Button type="button" onClick={handleContinue} disabled={isLoading || !canProceed} className="w-full">
          Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </motion.div>
    </div>
  );
}