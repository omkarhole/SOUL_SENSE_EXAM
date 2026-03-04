'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useSettings } from '@/hooks/useSettings';
import { useProfile } from '@/hooks/useProfile';
import { UserSettings } from '@/lib/api/settings';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AvatarUpload } from '@/components/profile/avatar-upload';
import { toast } from 'sonner';
import { Shield, Bell, Palette, User } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const { settings, isLoading: settingsLoading, error: settingsError, updateSettings } = useSettings();
  const { profile, isLoading: profileLoading, uploadAvatar } = useProfile();

  const handleThemeChange = async (theme: 'light' | 'dark' | 'system') => {
    try {
      await updateSettings({ theme });
      toast.success('Theme updated successfully');
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
      toast.success('Notification settings updated');
    } catch (err) {
      console.error('Failed to update notifications:', err);
      toast.error('Failed to update notifications. Please try again.');
    }
  };

  const handlePrivacyToggle = async (
    key: keyof UserSettings['privacy'],
    checked: boolean
  ) => {
    if (!settings) return;
    try {
      await updateSettings({
        privacy: {
          ...settings.privacy,
          [key]: checked,
        },
      });
      toast.success('Privacy settings updated');
    } catch (err) {
      console.error('Failed to update privacy:', err);
      toast.error('Failed to update privacy settings. Please try again.');
    }
  };

  if (settingsLoading || profileLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold mb-2">Settings</h1>
            <p className="text-muted-foreground">Manage your account preferences</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (settingsError) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-2">Settings</h1>
          <p className="text-red-500">Failed to load settings. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground">Manage your account preferences and profile</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Profile Avatar */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Profile Picture
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AvatarUpload
                currentAvatarPath={profile?.avatar_path}
                username={user?.username || 'User'}
                onUpload={uploadAvatar}
                onAvatarUpdate={(avatarPath: string) => {
                  toast.success('Avatar updated successfully');
                }}
              />
            </CardContent>
          </Card>

          {/* Theme */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Appearance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Theme</label>
                <Select value={settings?.theme || 'system'} onValueChange={handleThemeChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Email Notifications</label>
                <Checkbox
                  checked={settings?.notifications?.email || false}
                  onChange={(e) => handleNotificationToggle('email', e.target.checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Push Notifications</label>
                <Checkbox
                  checked={settings?.notifications?.push || false}
                  onChange={(e) => handleNotificationToggle('push', e.target.checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Privacy */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Privacy & Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Analytics Sharing</label>
                <Checkbox
                  checked={settings?.privacy?.analytics || false}
                  onChange={(e) => handlePrivacyToggle('analytics', e.target.checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Data Collection</label>
                <Checkbox
                  checked={settings?.privacy?.data_collection || false}
                  onChange={(e) => handlePrivacyToggle('data_collection', e.target.checked)}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}