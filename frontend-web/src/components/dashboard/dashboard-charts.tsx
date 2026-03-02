'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useFetchDashboardData } from '@/hooks/useDashboard';

interface FilterDropdownProps {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}

function FilterDropdown({ label, value, options, onChange }: FilterDropdownProps) {
  return (
    <div className="flex flex-col space-y-1">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function DashboardCharts() {
  const searchParams = useSearchParams();
  const { replace } = useRouter();
  const pathname = usePathname();
  const [isHydrated, setIsHydrated] = useState(false);

  const { data, loading, error } = useFetchDashboardData();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const handleFilterChange = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) params.set(key, value);
    else params.delete(key);
    replace(`${pathname}?${params.toString()}`);
  };

  const timeframe = searchParams.get('timeframe') || '30d';
  const examType = searchParams.get('exam_type') || '';
  const sentiment = searchParams.get('sentiment') || '';

  const timeframeOptions = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ];

  const examTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'standard', label: 'Standard' },
    { value: 'advanced', label: 'Advanced' },
  ];

  const sentimentOptions = [
    { value: '', label: 'All Sentiments' },
    { value: 'positive', label: 'Positive' },
    { value: 'neutral', label: 'Neutral' },
    { value: 'negative', label: 'Negative' },
  ];

  // Transform data for the chart
  const chartData = data?.historical_trends.map((point) => ({
    date: new Date(point.timestamp).toLocaleDateString(),
    score: point.total_score,
    sentiment: point.sentiment_score,
  })) || [];

  if (!isHydrated) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex flex-wrap gap-4 mb-6">
        <FilterDropdown
          label="Filter by Date"
          value={timeframe}
          options={timeframeOptions}
          onChange={(value) => handleFilterChange('timeframe', value)}
        />
        <FilterDropdown
          label="Filter by Exam Type"
          value={examType}
          options={examTypeOptions}
          onChange={(value) => handleFilterChange('exam_type', value)}
        />
        <FilterDropdown
          label="Filter by Sentiment"
          value={sentiment}
          options={sentimentOptions}
          onChange={(value) => handleFilterChange('sentiment', value)}
        />
      </div>

      {loading ? (
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      ) : error ? (
        <div className="text-red-600">Error loading chart data: {error.message}</div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} key={JSON.stringify({ timeframe, examType, sentiment })}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#8884d8"
                strokeWidth={2}
                dot={{ fill: '#8884d8' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}