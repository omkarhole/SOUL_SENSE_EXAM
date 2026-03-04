package com.soulsense;

/**
 * Centralized analytics event constants.
 * All event names must follow the strict naming convention:
 * - lowercase
 * - snake_case
 * - no spaces
 * - no camelCase
 * - no undocumented prefixes
 *
 * Event Schema Version: 1.0
 */
public final class AnalyticsEvents {

    private AnalyticsEvents() {
        // Utility class
    }

    // ============================================================================
    // SCREEN VIEW EVENTS
    // ============================================================================

    /** Screen view event for home screen */
    public static final String SCREEN_VIEW = "screen_view";

    /** Screen view event for login screen */
    public static final String LOGIN_SCREEN_VIEW = "login_screen_view";

    /** Screen view event for signup screen */
    public static final String SIGNUP_SCREEN_VIEW = "signup_screen_view";

    /** Screen view event for profile screen */
    public static final String PROFILE_SCREEN_VIEW = "profile_screen_view";

    /** Screen view event for settings screen */
    public static final String SETTINGS_SCREEN_VIEW = "settings_screen_view";

    // ============================================================================
    // USER INTERACTION EVENTS
    // ============================================================================

    /** Button click event */
    public static final String BUTTON_CLICK = "button_click";

    /** Start button click */
    public static final String START_BUTTON_CLICK = "start_button_click";

    /** Login button click */
    public static final String LOGIN_BUTTON_CLICK = "login_button_click";

    /** Signup button click */
    public static final String SIGNUP_BUTTON_CLICK = "signup_button_click";

    /** Logout button click */
    public static final String LOGOUT_BUTTON_CLICK = "logout_button_click";

    // ============================================================================
    // AUTHENTICATION EVENTS
    // ============================================================================

    /** Signup process started */
    public static final String SIGNUP_START = "signup_start";

    /** Signup completed successfully */
    public static final String SIGNUP_SUCCESS = "signup_success";

    /** Signup failed */
    public static final String SIGNUP_FAILURE = "signup_failure";

    /** Login attempt */
    public static final String LOGIN_ATTEMPT = "login_attempt";

    /** Login success */
    public static final String LOGIN_SUCCESS = "login_success";

    /** Login failure */
    public static final String LOGIN_FAILURE = "login_failure";

    // ============================================================================
    // PAYMENT EVENTS
    // ============================================================================

    /** Payment process started */
    public static final String PAYMENT_START = "payment_start";

    /** Payment completed successfully */
    public static final String PAYMENT_SUCCESS = "payment_success";

    /** Payment failed */
    public static final String PAYMENT_FAILURE = "payment_failure";

    // ============================================================================
    // FEATURE USAGE EVENTS
    // ============================================================================

    /** Journal entry created */
    public static final String JOURNAL_ENTRY_CREATED = "journal_entry_created";

    /** Assessment started */
    public static final String ASSESSMENT_STARTED = "assessment_started";

    /** Assessment completed */
    public static final String ASSESSMENT_COMPLETED = "assessment_completed";

    /** Report viewed */
    public static final String REPORT_VIEWED = "report_viewed";

    // ============================================================================
    // SYSTEM EVENTS
    // ============================================================================

    /** App launched */
    public static final String APP_LAUNCH = "app_launch";

    /** App backgrounded */
    public static final String APP_BACKGROUND = "app_background";

    /** App foregrounded */
    public static final String APP_FOREGROUND = "app_foreground";

    /** App crashed */
    public static final String APP_CRASH = "app_crash";

    /** Device rotated */
    public static final String DEVICE_ROTATION = "device_rotation";

    // ============================================================================
    // SESSION EVENTS
    // ============================================================================

    /** Session started */
    public static final String SESSION_START = "session_start";

    /** Session ended */
    public static final String SESSION_END = "session_end";

    // ============================================================================
    // ENGAGEMENT & BEHAVIOR EVENTS
    // ============================================================================

    /** 25% scroll depth reached */
    public static final String SCROLL_DEPTH_25 = "scroll_depth_25";

    /** 50% scroll depth reached */
    public static final String SCROLL_DEPTH_50 = "scroll_depth_50";

    /** 75% scroll depth reached */
    public static final String SCROLL_DEPTH_75 = "scroll_depth_75";

    /** 100% scroll depth reached */
    public static final String SCROLL_DEPTH_100 = "scroll_depth_100";

    // ============================================================================
    // SCREEN TIME TRACKING EVENTS
    // ============================================================================

    /** User entered a screen */
    public static final String SCREEN_ENTER = "screen_enter";

    /** User exited a screen */
    public static final String SCREEN_EXIT = "screen_exit";

    // ============================================================================
    // ERROR EVENTS
    // ============================================================================

    /** Network error occurred */
    public static final String NETWORK_ERROR = "network_error";

    /** API error occurred */
    public static final String API_ERROR = "api_error";

    /** Validation error occurred */
    public static final String VALIDATION_ERROR = "validation_error";

    /** Client-side validation failed */
    public static final String VALIDATION_FAILED = "validation_failed";
}