package com.soulsense.analytics;

/**
 * Mock network interceptor for API error tracking
 * In a real Android app, this would extend OkHttp Interceptor
 */
public class AnalyticsInterceptor {

    private final AnalyticsManager analyticsManager;

    public AnalyticsInterceptor(AnalyticsManager analyticsManager) {
        this.analyticsManager = analyticsManager;
    }

    /**
     * Mock intercept method - in real implementation would be:
     * public Response intercept(Chain chain) throws IOException
     *
     * This is a placeholder for testing purposes.
     * In production, integrate with actual HTTP client interceptor.
     */
    public void interceptRequest(String url, int responseCode, String errorMessage, long latency, int retryCount) {
        // Track API errors (4xx, 5xx status codes)
        if (responseCode >= 400) {
            analyticsManager.trackApiError(url, responseCode, errorMessage, latency, retryCount);
        }
    }

    /**
     * Mock method for handling network exceptions
     */
    public void interceptException(String url, String errorMessage, long latency, int retryCount) {
        analyticsManager.trackApiError(url, 0, errorMessage, latency, retryCount);
    }
}