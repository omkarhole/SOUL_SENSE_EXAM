'use client';

import React from 'react';
import { useController, Control, FieldValues, Path } from 'react-hook-form';
import { FormLabel } from './FormLabel';
import { FormError } from './FormError';
import { FormMessage } from './FormMessage';
import { Input } from '@/components/ui';
import { cn } from '@/lib/utils';

interface FormFieldProps<T extends FieldValues> extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'name' | 'children'
> {
  control: Control<T>;
  name: Path<T>;
  label?: string;
  children?: (field: any) => React.ReactNode;
}

export function FormField<T extends FieldValues>({
  control,
  name,
  label,
  placeholder,
  type = 'text',
  required = false,
  disabled = false,
  className = '',
  children,
  ...props
}: FormFieldProps<T>) {
  const {
    field,
    fieldState: { error },
  } = useController({
    name,
    control,
  });

  // Add error styling class when field has error
  const inputClassName = cn(
    className,
    error && 'border-destructive focus-visible:ring-destructive'
  );

  const fieldProps = {
    ...field,
    value: type === 'checkbox' || type === 'radio' ? field.value : (field.value ?? ''),
    ...props,
    placeholder,
    type,
    required,
    disabled,
    className: inputClassName,
    'aria-invalid': !!error,
    'aria-describedby': error ? `${name}-error` : undefined,
  };

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <FormLabel htmlFor={name} required={required}>
          {label}
        </FormLabel>
      )}
      {children ? children(fieldProps) : <Input {...fieldProps} />}
      <FormError error={error?.message} />
      <FormMessage name={name} />
    </div>
  );
}
