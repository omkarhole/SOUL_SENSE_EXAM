'use client';

import { UserSettings } from '../../lib/api/settings';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';
import { Button } from '@/components/ui';
import { Input } from '@/components/ui';
import { Label } from '@/components/ui';
import { useDebounceCallback } from '@/hooks/useDebounceCallback';
import { useId, useState } from 'react';
import { Globe, Clock, Calendar, Lock, Shield, Mail, Chrome } from 'lucide-react';

interface AccountSettingsProps {
  settings: UserSettings;
  onChange: (updates: Partial<UserSettings>) => void;
}

export function AccountSettings({ settings, onChange }: AccountSettingsProps) {
  const scopeId = useId();
  const currentPasswordId = `${scopeId}-current-password`;
  const newPasswordId = `${scopeId}-new-password`;
  const confirmPasswordId = `${scopeId}-confirm-password`;
  const debouncedOnChange = useDebounceCallback(onChange, 500);
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  const handleAccountChange = (key: 'language' | 'timezone' | 'date_format', value: string) => {
    debouncedOnChange({
      account: {
        ...settings.account,
        [key]: value,
      },
    });
  };

  const handlePasswordChange = (field: 'current' | 'new' | 'confirm', value: string) => {
    setPasswordData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePasswordSubmit = () => {
    if (passwordData.new !== passwordData.confirm) {
      return;
    }
    console.log('Changing password...');
    setPasswordData({ current: '', new: '', confirm: '' });
  };

  const handleConnectGoogle = () => {
    console.log('Connecting Google account...');
  };

  return (
    <div className="space-y-12">
      {/* Account Preferences */}
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Globe className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Regional Preferences</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="language" className="text-xs font-bold px-1">
              Language
            </Label>
            <Select
              value={settings.account.language}
              onValueChange={(value: string) => handleAccountChange('language', value)}
            >
              <SelectTrigger className="w-full h-11 rounded-xl bg-muted/10 border-border/40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-border/40">
                <SelectItem value="en">English (US)</SelectItem>
                <SelectItem value="es">Español</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
                <SelectItem value="de">Deutsch</SelectItem>
                <SelectItem value="ja">日本語</SelectItem>
                <SelectItem value="zh">中文</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone" className="text-xs font-bold px-1">
              Timezone
            </Label>
            <Select
              value={settings.account.timezone}
              onValueChange={(value: string) => handleAccountChange('timezone', value)}
            >
              <SelectTrigger className="w-full h-11 rounded-xl bg-muted/10 border-border/40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-border/40">
                <SelectItem value="UTC">Universal Time (UTC)</SelectItem>
                <SelectItem value="America/New_York">Eastern Time</SelectItem>
                <SelectItem value="America/Chicago">Central Time</SelectItem>
                <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                <SelectItem value="Europe/London">London</SelectItem>
                <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                <SelectItem value="Asia/Shanghai">Shanghai</SelectItem>
                <SelectItem value="Australia/Sydney">Sydney</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="date-format" className="text-xs font-bold px-1">
              Date Format
            </Label>
            <Select
              value={settings.account.date_format}
              onValueChange={(value: string) => handleAccountChange('date_format', value)}
            >
              <SelectTrigger className="w-full h-11 rounded-xl bg-muted/10 border-border/40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-border/40">
                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Password Change */}
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Lock className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">Security Credentials</h3>
        </div>

        <div className="grid grid-cols-1 gap-4 bg-muted/10 p-6 rounded-2xl border border-border/40">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={currentPasswordId} className="text-xs font-bold px-1">
                Current Password
              </Label>
              <Input
                id={currentPasswordId}
                type="password"
                value={passwordData.current}
                onChange={(e) => handlePasswordChange('current', e.target.value)}
                placeholder="Enter current password"
                className="h-11 rounded-xl bg-background border-border/60"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor={newPasswordId} className="text-xs font-bold px-1">
                  New Password
                </Label>
                <Input
                  id={newPasswordId}
                  type="password"
                  value={passwordData.new}
                  onChange={(e) => handlePasswordChange('new', e.target.value)}
                  placeholder="Create new password"
                  className="h-11 rounded-xl bg-background border-border/60"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={confirmPasswordId} className="text-xs font-bold px-1">
                  Confirm Password
                </Label>
                <Input
                  id={confirmPasswordId}
                  type="password"
                  value={passwordData.confirm}
                  onChange={(e) => handlePasswordChange('confirm', e.target.value)}
                  placeholder="Repeat new password"
                  className="h-11 rounded-xl bg-background border-border/60"
                />
              </div>
            </div>
          </div>

          <Button
            onClick={handlePasswordSubmit}
            disabled={!passwordData.current || !passwordData.new || !passwordData.confirm}
            className="w-full sm:w-auto font-black uppercase tracking-widest text-[10px] h-10 rounded-full mt-2"
          >
            Update Password
          </Button>
        </div>
      </div>

      {/* Connected Accounts */}
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <Shield className="h-3.5 w-3.5" />
          <h3 className="text-[10px] uppercase tracking-widest font-black">
            External Authorization
          </h3>
        </div>

        <div className="flex items-center justify-between p-5 bg-muted/10 border border-border/40 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="p-2.5 rounded-xl bg-background border border-border/40 text-muted-foreground">
              <Chrome className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-bold">Google Identity</p>
              <p className="text-[10px] text-muted-foreground font-medium">
                Use your Google account for faster access
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={handleConnectGoogle}
            className="font-black uppercase tracking-widest text-[10px] h-9 rounded-full px-6 border-border/60 hover:bg-primary/5 hover:text-primary transition-colors"
          >
            Connect
          </Button>
        </div>
      </div>
    </div>
  );
}
