package com.soulsense.analytics;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import java.util.UUID;
import java.util.Map;
import java.util.HashMap;

import com.soulsense.AnalyticsEvents;

/**
 * Analytics Manager for Android
 * Handles user identity and session tracking
 */
public class AnalyticsManager {

    private static final String TAG = "AnalyticsManager";
    private static final String PREFS_NAME = "analytics_prefs";
    private static final String GUEST_ID_KEY = "guest_user_id";
    private static final String CURRENT_USER_ID_KEY = "current_user_id";
    private static final String SESSION_START_TIME_KEY = "session_start_time";

    private static AnalyticsManager instance;
    private final SharedPreferences prefs;
    private final Context context;

    private String currentUserId;
    private String guestUserId;
    private String currentSessionId;
    private long sessionStartTime;
    private boolean isSessionActive = false;

    // Screen time tracking
    private String currentScreen;
    private long screenEnterTime;
    private String screenEnterTimestamp;

    private AnalyticsManager(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = this.context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        initializeUserIdentity();
        generateNewSessionId();
    }

    public static synchronized AnalyticsManager getInstance(Context context) {
        if (instance == null) {
            instance = new AnalyticsManager(context);
        }
        return instance;
    }

    private void initializeUserIdentity() {
        // Load or generate guest ID
        guestUserId = prefs.getString(GUEST_ID_KEY, null);
        if (guestUserId == null) {
            guestUserId = "guest_" + UUID.randomUUID().toString();
            prefs.edit().putString(GUEST_ID_KEY, guestUserId).apply();
            Log.d(TAG, "Generated new guest ID: " + guestUserId);
        }

        // Load current user ID (or use guest ID)
        currentUserId = prefs.getString(CURRENT_USER_ID_KEY, guestUserId);
    }

    private void generateNewSessionId() {
        currentSessionId = "session_" + System.currentTimeMillis() + "_" +
                          UUID.randomUUID().toString().substring(0, 9);
    }

    /**
     * Start a new session
     */
    public void startSession() {
        if (isSessionActive) return;

        sessionStartTime = System.currentTimeMillis();
        isSessionActive = true;

        prefs.edit().putLong(SESSION_START_TIME_KEY, sessionStartTime).apply();

        // Track session start event
        Map<String, Object> properties = new HashMap<>();
        trackEvent(AnalyticsEvents.SESSION_START, properties);

        Log.d(TAG, "Session started: " + currentSessionId);
    }

    /**
     * End the current session
     */
    public void endSession() {
        if (!isSessionActive) return;

        long sessionDuration = System.currentTimeMillis() - sessionStartTime;
        isSessionActive = false;

        // Track session end event
        Map<String, Object> properties = new HashMap<>();
        properties.put("session_duration_ms", sessionDuration);
        properties.put("session_duration_seconds", Math.round(sessionDuration / 1000.0));
        trackEvent(AnalyticsEvents.SESSION_END, properties);

        // Generate new session ID for next session
        generateNewSessionId();

        Log.d(TAG, "Session ended. Duration: " + sessionDuration + "ms");
    }

    /**
     * Set authenticated user ID (clears guest mode)
     */
    public void setUserId(String userId) {
        if (currentUserId.equals(guestUserId)) {
            // Clear guest ID from persistent storage when user logs in
            prefs.edit().remove(GUEST_ID_KEY).apply();
        }

        currentUserId = userId;
        prefs.edit().putString(CURRENT_USER_ID_KEY, userId).apply();

        Log.d(TAG, "User ID set: " + userId);
    }

    /**
     * Clear user ID (return to guest mode)
     */
    public void clearUserId() {
        currentUserId = guestUserId;
        prefs.edit().remove(CURRENT_USER_ID_KEY).apply();

        Log.d(TAG, "User ID cleared, back to guest mode");
    }

    /**
     * Get current user ID (authenticated user or guest)
     */
    public String getCurrentUserId() {
        return currentUserId;
    }

    /**
     * Get guest user ID
     */
    public String getGuestUserId() {
        return guestUserId;
    }

    /**
     * Get current session ID
     */
    public String getCurrentSessionId() {
        return currentSessionId;
    }

    /**
     * Check if session is currently active
     */
    public boolean isSessionActive() {
        return isSessionActive;
    }

    /**
     * Track an analytics event
     */
    public void trackEvent(String eventName, Map<String, Object> properties) {
        // Create analytics event with user and session context
        AnalyticsEvent event = new AnalyticsEvent(
            eventName,
            System.currentTimeMillis(),
            currentUserId,
            currentSessionId,
            "android",
            getAppVersion(),
            properties
        );

        // Send to analytics provider
        sendToAnalyticsProvider(event);
    }

    /**
     * Track screen view
     */
    public void trackScreenView(String screenName) {
        Map<String, Object> properties = new HashMap<>();
        properties.put("screen_name", screenName);
        trackEvent(AnalyticsEvents.SCREEN_VIEW, properties);
    }

    /**
     * Track button click
     */
    public void trackButtonClick(String buttonName) {
        Map<String, Object> properties = new HashMap<>();
        properties.put("button_name", buttonName);
        properties.put("element_type", "button");
        trackEvent(AnalyticsEvents.BUTTON_CLICK, properties);
    }

    /**
     * Track login success
     */
    public void trackLoginSuccess() {
        Map<String, Object> properties = new HashMap<>();
        trackEvent(AnalyticsEvents.LOGIN_SUCCESS, properties);
    }

    /**
     * Track logout
     */
    public void trackLogout() {
        Map<String, Object> properties = new HashMap<>();
        trackEvent(AnalyticsEvents.LOGOUT_BUTTON_CLICK, properties);
    }

    /**
     * Track scroll depth reached
     */
    public void trackScrollDepth(int percentage, String screenName) {
        String eventName;
        switch (percentage) {
            case 25:
                eventName = AnalyticsEvents.SCROLL_DEPTH_25;
                break;
            case 50:
                eventName = AnalyticsEvents.SCROLL_DEPTH_50;
                break;
            case 75:
                eventName = AnalyticsEvents.SCROLL_DEPTH_75;
                break;
            case 100:
                eventName = AnalyticsEvents.SCROLL_DEPTH_100;
                break;
            default:
                Log.w(TAG, "Invalid scroll percentage: " + percentage);
                return;
        }

        Map<String, Object> properties = new HashMap<>();
        properties.put("scroll_percentage", percentage);
        properties.put("screen_name", screenName);
        trackEvent(eventName, properties);
    }

    /**
     * Track screen enter for time tracking
     */
    public void enterScreen(String screenName) {
        // Exit current screen if any
        if (currentScreen != null) {
            exitScreen("navigation");
        }

        // Enter new screen
        currentScreen = screenName;
        screenEnterTime = System.currentTimeMillis();
        screenEnterTimestamp = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
            .format(new java.util.Date(screenEnterTime));

        Map<String, Object> properties = new HashMap<>();
        properties.put("screen_name", screenName);
        properties.put("enter_time", screenEnterTimestamp);
        trackEvent(AnalyticsEvents.SCREEN_ENTER, properties);
    }

    /**
     * Track screen exit with duration
     */
    public void exitScreen(String exitReason) {
        if (currentScreen == null || screenEnterTime == 0) return;

        long exitTime = System.currentTimeMillis();
        String exitTimestamp = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
            .format(new java.util.Date(exitTime));
        long durationMs = exitTime - screenEnterTime;
        long durationSeconds = Math.round(durationMs / 1000.0);

        Map<String, Object> properties = new HashMap<>();
        properties.put("screen_name", currentScreen);
        properties.put("enter_time", screenEnterTimestamp);
        properties.put("exit_time", exitTimestamp);
        properties.put("duration_ms", durationMs);
        properties.put("duration_seconds", durationSeconds);
        properties.put("exit_reason", exitReason);
        trackEvent(AnalyticsEvents.SCREEN_EXIT, properties);

        // Reset screen tracking
        currentScreen = null;
        screenEnterTime = 0;
        screenEnterTimestamp = null;
    }

    /**
     * Track API error with detailed information
     */
    public void trackApiError(String endpoint, int responseCode, String errorMessage, long latency, int retryCount) {
        Map<String, Object> properties = new HashMap<>();
        properties.put("endpoint", endpoint);
        properties.put("response_code", responseCode);
        properties.put("error_message", errorMessage);
        properties.put("latency", latency);
        properties.put("retry_count", retryCount);
        trackEvent(AnalyticsEvents.API_ERROR, properties);
    }

    /**
     * Track client-side validation failure
     */
    public void trackValidationFailure(String fieldName, String reason) {
        Map<String, Object> properties = new HashMap<>();
        properties.put("field_name", fieldName);
        properties.put("reason", reason);
        trackEvent(AnalyticsEvents.VALIDATION_FAILED, properties);
    }

    /**
     * Get network interceptor for automatic API error tracking
     * Usage: analyticsManager.getNetworkInterceptor().interceptRequest(url, code, message, latency, retryCount);
     */
    public AnalyticsInterceptor getNetworkInterceptor() {
        return new AnalyticsInterceptor(this);
    }

    private String getAppVersion() {
        try {
            // Mock implementation for non-Android environment
            return "1.0.0";
        } catch (Exception e) {
            return "1.0.0";
        }
    }

    private void sendToAnalyticsProvider(AnalyticsEvent event) {
        // Basic implementation: log to console
        // Future enhancement: Integrate with analytics provider (Firebase, Mixpanel, etc.)
        Log.i(TAG, String.format("Analytics Event: %s | User: %s | Session: %s | Props: %s",
            event.getEventName(),
            event.getUserId(),
            event.getSessionId(),
            event.getProperties().toString()));
    }

    /**
     * Analytics Event data class
     */
    public static class AnalyticsEvent {
        private final String eventName;
        private final long timestamp;
        private final String userId;
        private final String sessionId;
        private final String platform;
        private final String appVersion;
        private final Map<String, Object> properties;

        public AnalyticsEvent(String eventName, long timestamp, String userId,
                            String sessionId, String platform, String appVersion,
                            Map<String, Object> properties) {
            this.eventName = eventName;
            this.timestamp = timestamp;
            this.userId = userId;
            this.sessionId = sessionId;
            this.platform = platform;
            this.appVersion = appVersion;
            this.properties = properties != null ? properties : new HashMap<>();
        }

        public String getEventName() { return eventName; }
        public long getTimestamp() { return timestamp; }
        public String getUserId() { return userId; }
        public String getSessionId() { return sessionId; }
        public String getPlatform() { return platform; }
        public String getAppVersion() { return appVersion; }
        public Map<String, Object> getProperties() { return properties; }
    }
}