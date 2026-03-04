//
//  AnalyticsNetworkInterceptor.swift
//  SoulSense
//
//  Network interceptor for automatic API error tracking
//

import Foundation

public class AnalyticsNetworkInterceptor: NSObject, URLSessionDelegate, URLSessionTaskDelegate {

    private let analyticsManager: AnalyticsManager
    private var requestStartTimes: [URLSessionTask: TimeInterval] = [:]
    private var retryCounts: [URLSessionTask: Int] = [:]

    public init(analyticsManager: AnalyticsManager) {
        self.analyticsManager = analyticsManager
        super.init()
    }

    // MARK: - URLSessionTaskDelegate

    public func urlSession(_ session: URLSession, task: URLSessionTask, didFinishCollecting metrics: URLSessionTaskMetrics) {
        // Store request start time
        requestStartTimes[task] = metrics.taskInterval.startDate.timeIntervalSince1970
    }

    public func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        let startTime = requestStartTimes[task] ?? Date().timeIntervalSince1970
        let latency = Date().timeIntervalSince1970 - startTime
        let retryCount = retryCounts[task] ?? 0
        let url = task.originalRequest?.url?.absoluteString ?? "unknown"

        if let error = error {
            // Track network/timeout errors
            analyticsManager.trackApiError(
                endpoint: url,
                responseCode: 0,
                errorMessage: error.localizedDescription,
                latency: latency,
                retryCount: retryCount
            )
        } else if let response = task.response as? HTTPURLResponse {
            // Track HTTP errors (4xx, 5xx)
            if !(200...299).contains(response.statusCode) {
                var errorMessage = "HTTP \(response.statusCode)"

                // Try to extract error message from response
                if let data = task.originalRequest?.httpBody,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let message = json["message"] as? String {
                    errorMessage = message
                } else if let statusMessage = HTTPURLResponse.localizedString(forStatusCode: response.statusCode),
                          !statusMessage.isEmpty {
                    errorMessage = statusMessage
                }

                analyticsManager.trackApiError(
                    endpoint: url,
                    responseCode: response.statusCode,
                    errorMessage: errorMessage,
                    latency: latency,
                    retryCount: retryCount
                )
            }
        }

        // Clean up
        requestStartTimes[task] = nil
        retryCounts[task] = nil
    }

    // MARK: - Helper Methods

    /**
     * Increment retry count for a task (call this when retrying requests)
     */
    public func incrementRetryCount(for task: URLSessionTask) {
        retryCounts[task] = (retryCounts[task] ?? 0) + 1
    }

    /**
     * Create URLSession with analytics interceptor
     */
    public func createSession() -> URLSession {
        let configuration = URLSessionConfiguration.default
        return URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
    }
}