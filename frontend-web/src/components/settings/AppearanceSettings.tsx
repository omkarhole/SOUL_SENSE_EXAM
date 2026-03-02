'use client';

import { UserSettings } from '../../lib/api/settings';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui';
import { Checkbox } from '../ui';
import { useDebounceCallback } from '../../hooks/useDebounceCallback';
import { ThemeToggle } from './theme-toggle';
import { Sun, Moon, Monitor, Type, Eye } from 'lucide-react';

interface AppearanceSettingsProps {
  settings: UserSettings;
  onChange: (updates: Partial<UserSettings>) => void;
}

export function AppearanceSettings({ settings, onChange }: AppearanceSettingsProps) {
  const debouncedOnChange = useDebounceCallback(onChange, 500);

  const handleThemeChange = (theme: 'light' | 'dark' | 'system') => {
    debouncedOnChange({ theme });
  };

  const handleAccessibilityChange = (key: 'high_contrast' | 'reduced_motion', value: boolean) => {
    debouncedOnChange({
      accessibility: {
        ...settings.accessibility,
        [key]: value,
      },
    });
  };

  const handleFontSizeChange = (fontSize: 'small' | 'medium' | 'large') => {
    debouncedOnChange({
      accessibility: {
        ...settings.accessibility,
        font_size: fontSize,
      },
    });
  };

  return (
    <div className="space-y-10">
      {/* Theme Selection */}
      <ThemeToggle
        value={settings.theme as 'light' | 'dark' | 'system'}
        onChange={handleThemeChange}
      />

      {/* Font Size */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Type className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Content Typography</h3>
        </div>
        <Select value={settings.accessibility.font_size} onValueChange={handleFontSizeChange}>
          <SelectTrigger className="w-full h-12 rounded-xl bg-muted/10 border-border/40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="rounded-xl border-border/40">
            <SelectItem value="small">Comfortable (Small)</SelectItem>
            <SelectItem value="medium">Standard (Medium)</SelectItem>
            <SelectItem value="large">Spacious (Large)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Accessibility Options */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Eye className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Visual Accessibility</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-4 rounded-2xl bg-muted/10 border border-border/40 group hover:border-border transition-colors">
            <div className="space-y-0.5">
              <p className="text-sm font-bold">High Contrast</p>
              <p className="text-[10px] text-muted-foreground font-medium">
                Prioritize legibility over aesthetics
              </p>
            </div>
            <Checkbox
              checked={settings.accessibility.high_contrast}
              onChange={(e) => handleAccessibilityChange('high_contrast', e.target.checked)}
              className="h-5 w-5 rounded-lg border-2 border-border/60"
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-2xl bg-muted/10 border border-border/40 group hover:border-border transition-colors">
            <div className="space-y-0.5">
              <p className="text-sm font-bold">Reduced Motion</p>
              <p className="text-[10px] text-muted-foreground font-medium">
                Minimize animations and transitions
              </p>
            </div>
            <Checkbox
              checked={settings.accessibility.reduced_motion}
              onChange={(e) => handleAccessibilityChange('reduced_motion', e.target.checked)}
              className="h-5 w-5 rounded-lg border-2 border-border/60"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
