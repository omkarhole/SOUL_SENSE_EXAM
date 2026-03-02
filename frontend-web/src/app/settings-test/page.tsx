'use client';

import { UserSettings } from '@/lib/api/settings';
import { useSettings } from '@/hooks/useSettings';
import { Button } from '@/components/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { Skeleton } from '@/components/ui';
import { Checkbox } from '@/components/ui';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui';
import { toast } from '@/lib/toast';

export default function SettingsTestPage() {
  const { settings, isLoading, error, updateSettings, syncSettings } = useSettings();

  const handleThemeChange = async (theme: 'light' | 'dark' | 'system') => {
    try {
      await updateSettings({ theme });
    } catch (err) {
      console.error('Failed to update theme:', err);
      toast.error('Failed to update theme. Please try again.');
    }
  };

  const handleNotificationToggle = async (
    key: keyof UserSettings['notifications'],
    checked: boolean
  ) => {
    if (!settings) return;
    try {
      await updateSettings({
        notifications: {
          ...settings.notifications,
          [key]: checked,
        },
      });
    } catch (err) {
      console.error('Failed to update notifications:', err);
      toast.error('Failed to update notifications. Please try again.');
    }
  };

  const handleSync = async () => {
    try {
      await syncSettings();
    } catch (err) {
      console.error('Failed to sync settings:', err);
      toast.error('Failed to sync settings. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <Card className="border-red-200">
          <CardContent className="p-6">
            <p className="text-red-600">Error loading settings: {error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <Card>
          <CardContent className="p-6">
            <p className="text-muted-foreground">No settings available</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Settings Test</h1>
        <Button onClick={handleSync} disabled={isLoading}>
          Sync Settings
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Theme Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={settings.theme} onValueChange={handleThemeChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Email</label>
              <Checkbox
                checked={settings.notifications.email}
                onChange={(e) => handleNotificationToggle('email', e.target.checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Push</label>
              <Checkbox
                checked={settings.notifications.push}
                onChange={(e) => handleNotificationToggle('push', e.target.checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy */}
        <Card>
          <CardHeader>
            <CardTitle>Privacy</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Share Analytics</label>
              <Checkbox
                checked={settings.privacy.analytics}
                onChange={(e) =>
                  updateSettings({
                    privacy: { ...settings.privacy, analytics: e.target.checked },
                  })
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium">Data Retention (days)</label>
              <p className="text-sm text-muted-foreground mt-1">
                {settings.privacy.data_retention_days} days
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Accessibility */}
        <Card>
          <CardHeader>
            <CardTitle>Accessibility</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">High Contrast</label>
              <Checkbox
                checked={settings.accessibility.high_contrast}
                onChange={(e) =>
                  updateSettings({
                    accessibility: { ...settings.accessibility, high_contrast: e.target.checked },
                  })
                }
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Reduced Motion</label>
              <Checkbox
                checked={settings.accessibility.reduced_motion}
                onChange={(e) =>
                  updateSettings({
                    accessibility: { ...settings.accessibility, reduced_motion: e.target.checked },
                  })
                }
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
