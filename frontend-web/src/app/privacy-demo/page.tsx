'use client';

import { useState } from 'react';
import { PrivacySettingsPremium } from '@/components/settings';
import { toast } from '@/lib/toast';

export default function PrivacyDemoPage() {
  const [settings, setSettings] = useState({
    analyticsSharing: true,
    dataRetention: '90_days',
    dataUsageSummary: {
      totalRecords: 12450,
      storageUsed: '42.5 MB',
      accountAge: '1.2 years',
      lastExport: '2025-12-15',
    },
  });

  const handleSettingsChange = (updated: any) => {
    setSettings((prev) => ({ ...prev, ...updated }));
  };

  const handleExport = async () => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 3000));
    console.log('Data exported successfully');
  };

  const handleDeleteAccount = async (password: string) => {
    // Simulate API call
    console.log('Deleting account with password:', password);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    toast.success('Account deleted simulation complete.');
  };

  return (
    <div className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-4xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-extrabold tracking-tight">Component Demo</h1>
          <p className="text-muted-foreground text-lg">
            Testing the Privacy & Data Management interface
          </p>
        </div>

        <div className="bg-card p-6 rounded-3xl border shadow-2xl">
          <PrivacySettingsPremium
            settings={settings}
            onChange={handleSettingsChange}
            onExportData={handleExport}
            onDeleteAccount={handleDeleteAccount}
          />
        </div>

        <div className="bg-muted p-6 rounded-2xl border">
          <h3 className="font-bold mb-4">Current State Debug:</h3>
          <pre className="text-xs bg-black text-green-400 p-4 rounded overflow-auto">
            {JSON.stringify(settings, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
