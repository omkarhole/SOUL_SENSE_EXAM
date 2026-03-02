import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api/client';

interface DashboardStatistics {
  historical_trends: Array<{
    id: number;
    timestamp: string;
    total_score: number;
    sentiment_score?: number;
  }>;
}

export function useFetchDashboardData() {
  const searchParams = useSearchParams();

  const timeframe = searchParams.get('timeframe') || '30d';
  const examType = searchParams.get('exam_type');
  const sentiment = searchParams.get('sentiment');

  const { data, isLoading: loading, error } = useQuery({
    queryKey: ['dashboard-stats', timeframe, examType, sentiment],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('timeframe', timeframe);
      if (examType) params.set('exam_type', examType);
      if (sentiment) params.set('sentiment', sentiment);

      const response = await apiClient<DashboardStatistics>(
        `/analytics/statistics?${params.toString()}`
      );
      return response;
    },
  });

  return { data, loading, error };
}