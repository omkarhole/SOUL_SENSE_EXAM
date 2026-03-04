'use client';

import { UserSettings } from '../../lib/api/settings';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';
import { Checkbox } from '@/components/ui';
import { useDebounceCallback } from '@/hooks/useDebounceCallback';
import { Mail, Smartphone, Clock, Book, Activity, Cpu, BellRing } from 'lucide-react';

interface NotificationSettingsProps {
  settings: UserSettings;
  onChange: (updates: Partial<UserSettings>) => void;
}

export function NotificationSettings({ settings, onChange }: NotificationSettingsProps) {
  const debouncedOnChange = useDebounceCallback(onChange, 500);

  const handleNotificationChange = (key: 'email' | 'push', value: boolean) => {
    debouncedOnChange({
      notifications: {
        ...settings.notifications,
        [key]: value,
      },
    });
  };

  const handleFrequencyChange = (frequency: 'immediate' | 'daily' | 'weekly') => {
    debouncedOnChange({
      notifications: {
        ...settings.notifications,
        frequency,
      },
    });
  };

  const handleTypeChange = (type: keyof UserSettings['notifications']['types'], value: boolean) => {
    debouncedOnChange({
      notifications: {
        ...settings.notifications,
        types: {
          ...settings.notifications.types,
          [type]: value,
        },
      },
    });
  };

  return (
    <div className="space-y-12">
      {/* General Configuration */}
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <BellRing className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Delivery Channels</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-5 bg-muted/10 border border-border/40 rounded-2xl group hover:border-border transition-all">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                <Mail className="h-5 w-5" />
              </div>
              <div className="space-y-0.5">
                <p className="text-sm font-bold">Email Notifications</p>
                <p className="text-[10px] text-muted-foreground font-medium">
                  Critical alerts via official email
                </p>
              </div>
            </div>
            <Checkbox
              checked={settings.notifications.email}
              onChange={(e) => handleNotificationChange('email', e.target.checked)}
              className="h-6 w-6 rounded-lg border-2 border-border/60"
            />
          </div>

          <div className="flex items-center justify-between p-5 bg-muted/10 border border-border/40 rounded-2xl group hover:border-border transition-all">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-xl bg-background border border-border/40 text-muted-foreground group-hover:text-primary transition-colors">
                <Smartphone className="h-5 w-5" />
              </div>
              <div className="space-y-0.5">
                <p className="text-sm font-bold">Push Notifications</p>
                <p className="text-[10px] text-muted-foreground font-medium">
                  Direct browser & app alerts
                </p>
              </div>
            </div>
            <Checkbox
              checked={settings.notifications.push}
              onChange={(e) => handleNotificationChange('push', e.target.checked)}
              className="h-6 w-6 rounded-lg border-2 border-border/60"
            />
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2 text-muted-foreground/60 mb-4">
            <Clock className="h-3.5 w-3.5" />
            <span className="text-[10px] uppercase tracking-widest font-black">
              Digest Frequency
            </span>
          </div>
          <Select value={settings.notifications.frequency} onValueChange={handleFrequencyChange}>
            <SelectTrigger className="w-full h-12 rounded-xl bg-muted/10 border-border/40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl border-border/40">
              <SelectItem value="immediate">Real-time (Immediate)</SelectItem>
              <SelectItem value="daily">Morning Digest (Daily)</SelectItem>
              <SelectItem value="weekly">Executive Summary (Weekly)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Subscription Types */}
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Activity className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Content Subscription</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              id: 'exam_reminders',
              label: 'Exam Reminders',
              desc: 'Upcoming assessment alerts',
              icon: Clock,
            },
            {
              id: 'journal_prompts',
              label: 'Journal Prompts',
              desc: 'Daily self-reflection questions',
              icon: Book,
            },
            {
              id: 'progress_updates',
              label: 'Progress Updates',
              desc: 'Growth analytics reports',
              icon: Activity,
            },
            {
              id: 'system_updates',
              label: 'System Updates',
              desc: 'New features and security',
              icon: Cpu,
            },
          ].map((type) => (
            <div
              key={type.id}
              className="flex items-center justify-between p-4 bg-muted/5 border border-border/40 rounded-2xl"
            >
              <div className="flex items-center gap-3">
                <type.icon className="h-4 w-4 text-muted-foreground/60" />
                <div className="space-y-0.5">
                  <p className="text-xs font-bold">{type.label}</p>
                  <p className="text-[9px] text-muted-foreground font-medium uppercase tracking-tight">
                    {type.desc}
                  </p>
                </div>
              </div>
              <Checkbox
                checked={
                  settings.notifications.types[type.id as keyof typeof settings.notifications.types]
                }
                onChange={(e) => handleTypeChange(type.id as any, e.target.checked)}
                className="h-5 w-5 rounded-md border-2 border-border/60"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
