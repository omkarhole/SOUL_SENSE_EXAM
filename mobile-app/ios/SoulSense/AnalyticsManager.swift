//
//  AnalyticsManager.swift
//  SoulSense
//
//  Analytics Manager for iOS
//  Handles user identity and session tracking
//

import Foundation
import UIKit
import Mixpanel

public class AnalyticsManager {

    private static var instance: AnalyticsManager?
    private let userDefaults = UserDefaults.standard

    private enum Keys {
        static let guestUserId = "analytics_guest_id"
        static let currentUserId = "analytics_current_user_id"
        static let sessionStartTime = "analytics_session_start_time"
    }

    private var currentUserId: String
    private var guestUserId: String
    private var currentSessionId: String
    private var sessionStartTime: TimeInterval = 0
    private var isSessionActive = false

    // Screen time tracking properties
    private var currentScreen: String?
    private var screenEnterTime: TimeInterval = 0
    private var screenEnterTimestamp: String?

    private init() {
        initializeMixpanel()
        initializeUserIdentity()
        generateNewSessionId()
        setupSessionTracking()
    }

    private func initializeMixpanel() {
        // TODO: Replace with your actual Mixpanel project token
        let token = "YOUR_MIXPANEL_PROJECT_TOKEN"
        
        #if DEBUG
        // Use a development token if available
        let devToken = "YOUR_MIXPANEL_DEV_TOKEN"
        Mixpanel.initialize(token: devToken)
        #else
        Mixpanel.initialize(token: token)
        #endif
        
        // Configure Mixpanel
        Mixpanel.mainInstance().loggingEnabled = true
        Mixpanel.mainInstance().trackAppLifecycleEvents = true
    }

    public static func shared() -> AnalyticsManager {
        if instance == nil {
            instance = AnalyticsManager()
        }
        return instance!
    }

    private func initializeUserIdentity() {
        // Load or generate guest ID
        if let storedGuestId = userDefaults.string(forKey: Keys.guestUserId) {
            guestUserId = storedGuestId
        } else {
            guestUserId = "guest_\(Date().timeIntervalSince1970)_\(UUID().uuidString.prefix(9))"
            userDefaults.set(guestUserId, forKey: Keys.guestUserId)
            print("[Analytics] Generated new guest ID: \(guestUserId)")
        }

        // Load current user ID (or use guest ID)
        currentUserId = userDefaults.string(forKey: Keys.currentUserId) ?? guestUserId
        
        // Identify user in Mixpanel
        Mixpanel.mainInstance().identify(distinctId: currentUserId)
        
        // Set super properties that will be sent with every event
        Mixpanel.mainInstance().registerSuperProperties([
            "platform": "ios",
            "app_version": getAppVersion(),
            "device_model": UIDevice.current.model,
            "os_version": UIDevice.current.systemVersion
        ])
    }

    private func generateNewSessionId() {
        currentSessionId = "session_\(Date().timeIntervalSince1970)_\(UUID().uuidString.prefix(9))"
        // Also update Mixpanel session property
        Mixpanel.mainInstance().registerSuperProperties(["session_id": currentSessionId])
    }

    private func setupSessionTracking() {
        // Track app lifecycle events
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidBecomeActive),
            name: UIApplication.didBecomeActiveNotification,
            object: nil
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidEnterBackground),
            name: UIApplication.didEnterBackgroundNotification,
            object: nil
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appWillTerminate),
            name: UIApplication.willTerminateNotification,
            object: nil
        )
    }

    @objc private func appDidBecomeActive() {
        startSession()
    }

    @objc private func appDidEnterBackground() {
        endSession()
    }

    @objc private func appWillTerminate() {
        endSession()
    }

    // MARK: - Session Management

    public func startSession() {
        guard !isSessionActive else { return }

        sessionStartTime = Date().timeIntervalSince1970
        isSessionActive = true

        userDefaults.set(sessionStartTime, forKey: Keys.sessionStartTime)

        // Track session start event
        trackEvent(AnalyticsEvents.sessionStart, properties: [:])

        print("[Analytics] Session started: \(currentSessionId)")
    }

    public func endSession() {
        guard isSessionActive else { return }

        let sessionDuration = Date().timeIntervalSince1970 - sessionStartTime
        isSessionActive = false

        // Track session end event
        let properties: [String: Any] = [
            "session_duration_ms": sessionDuration * 1000,
            "session_duration_seconds": round(sessionDuration)
        ]
        trackEvent(AnalyticsEvents.sessionEnd, properties: properties)

        // Generate new session ID for next session
        generateNewSessionId()

        print("[Analytics] Session ended. Duration: \(sessionDuration)s")
    }

    // MARK: - User Identity Management

    public func setUserId(_ userId: String) {
        let isReturningGuest = (currentUserId == guestUserId)
        
        if isReturningGuest {
            // Alias helps link guest activity to the new user account in Mixpanel
            Mixpanel.mainInstance().createAlias(userId, distinctId: guestUserId)
            userDefaults.removeObject(forKey: Keys.guestUserId)
        }

        currentUserId = userId
        userDefaults.set(userId, forKey: Keys.currentUserId)
        
        // Re-identify with the real user ID
        Mixpanel.mainInstance().identify(distinctId: userId)
        
        // Update user profile properties (People Analytics)
        Mixpanel.mainInstance().people.set(properties: [
            "$last_login": Date(),
            "user_id": userId
        ])

        print("[Analytics] User ID set: \(userId)")
    }

    public func clearUserId() {
        currentUserId = guestUserId
        userDefaults.removeObject(forKey: Keys.currentUserId)
        
        // Reset Mixpanel state for the next user
        Mixpanel.mainInstance().reset()
        
        // Re-identify as guest
        Mixpanel.mainInstance().identify(distinctId: guestUserId)

        print("[Analytics] User ID cleared, back to guest mode")
    }

    public func getCurrentUserId() -> String {
        return currentUserId
    }

    public func getGuestUserId() -> String {
        return guestUserId
    }

    public func getCurrentSessionId() -> String {
        return currentSessionId
    }

    public func isSessionActive() -> Bool {
        return isSessionActive
    }

    // MARK: - Event Tracking

    public func trackEvent(_ eventName: String, properties: [String: Any] = [:]) {
        let event = AnalyticsEvent(
            eventName: eventName,
            timestamp: Date().timeIntervalSince1970,
            userId: currentUserId,
            sessionId: currentSessionId,
            platform: "ios",
            appVersion: getAppVersion(),
            properties: properties
        )

        // Send to analytics provider
        sendToAnalyticsProvider(event)
    }

    public func trackScreenView(_ screenName: String) {
        trackEvent(AnalyticsEvents.screenView, properties: ["screen_name": screenName])
    }

    public func trackButtonClick(_ buttonName: String) {
        trackEvent(AnalyticsEvents.buttonClick, properties: [
            "button_name": buttonName,
            "element_type": "button"
        ])
    }

    public func trackLoginSuccess() {
        trackEvent(AnalyticsEvents.loginSuccess, properties: [:])
    }

    public func trackLogout() {
        trackEvent(AnalyticsEvents.logoutButtonClick, properties: [:])
    }

    public func trackScrollDepth(_ percentage: Int, screenName: String) {
        let eventName: String
        switch percentage {
        case 25:
            eventName = AnalyticsEvents.scrollDepth25
        case 50:
            eventName = AnalyticsEvents.scrollDepth50
        case 75:
            eventName = AnalyticsEvents.scrollDepth75
        case 100:
            eventName = AnalyticsEvents.scrollDepth100
        default:
            print("[Analytics] Warning: Invalid scroll percentage: \(percentage)")
            return
        }

        trackEvent(eventName, properties: [
            "scroll_percentage": percentage,
            "screen_name": screenName
        ])
    }

    /**
     * Track screen enter for time tracking
     */
    public func enterScreen(_ screenName: String) {
        // Exit current screen if any
        if currentScreen != nil {
            exitScreen("navigation")
        }

        // Enter new screen
        currentScreen = screenName
        screenEnterTime = Date().timeIntervalSince1970
        let dateFormatter = ISO8601DateFormatter()
        screenEnterTimestamp = dateFormatter.string(from: Date())

        trackEvent(AnalyticsEvents.screenEnter, properties: [
            "screen_name": screenName,
            "enter_time": screenEnterTimestamp!
        ])
    }

    /**
     * Track screen exit with duration
     */
    public func exitScreen(_ exitReason: String) {
        guard let screenName = currentScreen, screenEnterTime > 0 else { return }

        let exitTime = Date().timeIntervalSince1970
        let dateFormatter = ISO8601DateFormatter()
        let exitTimestamp = dateFormatter.string(from: Date())
        let durationMs = (exitTime - screenEnterTime) * 1000
        let durationSeconds = round(exitTime - screenEnterTime)

        trackEvent(AnalyticsEvents.screenExit, properties: [
            "screen_name": screenName,
            "enter_time": screenEnterTimestamp!,
            "exit_time": exitTimestamp,
            "duration_ms": durationMs,
            "duration_seconds": durationSeconds,
            "exit_reason": exitReason
        ])

        // Reset screen tracking
        currentScreen = nil
        screenEnterTime = 0
        screenEnterTimestamp = nil
    }

    /**
     * Track API error with detailed information
     */
    public func trackApiError(endpoint: String, responseCode: Int, errorMessage: String, latency: TimeInterval, retryCount: Int = 0) {
        trackEvent(AnalyticsEvents.apiError, properties: [
            "endpoint": endpoint,
            "response_code": responseCode,
            "error_message": errorMessage,
            "latency": latency,
            "retry_count": retryCount
        ])
    }

    /**
     * Track client-side validation failure
     */
    public func trackValidationFailure(fieldName: String, reason: String) {
        trackEvent(AnalyticsEvents.validationFailed, properties: [
            "field_name": fieldName,
            "reason": reason
        ])
    }

    /**
     * Get network interceptor for automatic API error tracking
     * Usage: let session = analyticsManager.getNetworkInterceptor().createSession()
     */
    public func getNetworkInterceptor() -> AnalyticsNetworkInterceptor {
        return AnalyticsNetworkInterceptor(analyticsManager: self)
    }

    private func getAppVersion() -> String {
        if let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String {
            return version
        }
        return "1.0.0"
    }

    private func sendToAnalyticsProvider(_ event: AnalyticsEvent) {
        // Real Mixpanel Integration
        var mixpanelProperties: [String: MixpanelType] = [:]
        
        // Convert internal properties to Mixpanel types
        for (key, value) in event.properties {
            if let mpValue = value as? MixpanelType {
                mixpanelProperties[key] = mpValue
            } else {
                mixpanelProperties[key] = String(describing: value)
            }
        }
        
        // Track the event in Mixpanel
        Mixpanel.mainInstance().track(event: event.eventName, properties: mixpanelProperties)
        
        print("[Analytics] Sent to Mixpanel: \(event.eventName)")
    }
}

// MARK: - Analytics Event Model

public struct AnalyticsEvent {
    public let eventName: String
    public let timestamp: TimeInterval
    public let userId: String
    public let sessionId: String
    public let platform: String
    public let appVersion: String
    public let properties: [String: Any]

    public init(eventName: String, timestamp: TimeInterval, userId: String,
                sessionId: String, platform: String, appVersion: String,
                properties: [String: Any]) {
        self.eventName = eventName
        self.timestamp = timestamp
        self.userId = userId
        self.sessionId = sessionId
        self.platform = platform
        self.appVersion = appVersion
        self.properties = properties
    }
}