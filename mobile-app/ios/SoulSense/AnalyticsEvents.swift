//
//  AnalyticsEvents.swift
//  SoulSense
//
//  Centralized analytics event constants.
//  All event names must follow the strict naming convention:
//  - lowercase
//  - snake_case
//  - no spaces
//  - no camelCase
//  - no undocumented prefixes
//
//  Event Schema Version: 1.0
//

import Foundation

public final class AnalyticsEvents {

    private init() {
        // Utility class
    }

    // ============================================================================
    // SCREEN VIEW EVENTS
    // ============================================================================

    /// Screen view event for home screen
    public static let screenView = "screen_view"

    /// Screen view event for login screen
    public static let loginScreenView = "login_screen_view"

    /// Screen view event for signup screen
    public static let signupScreenView = "signup_screen_view"

    /// Screen view event for profile screen
    public static let profileScreenView = "profile_screen_view"

    /// Screen view event for settings screen
    public static let settingsScreenView = "settings_screen_view"

    // ============================================================================
    // USER INTERACTION EVENTS
    // ============================================================================

    /// Button click event
    public static let buttonClick = "button_click"

    /// Start button click
    public static let startButtonClick = "start_button_click"

    /// Login button click
    public static let loginButtonClick = "login_button_click"

    /// Signup button click
    public static let signupButtonClick = "signup_button_click"

    /// Logout button click
    public static let logoutButtonClick = "logout_button_click"

    // ============================================================================
    // AUTHENTICATION EVENTS
    // ============================================================================

    /// Signup process started
    public static let signupStart = "signup_start"

    /// Signup completed successfully
    public static let signupSuccess = "signup_success"

    /// Signup failed
    public static let signupFailure = "signup_failure"

    /// Login attempt
    public static let loginAttempt = "login_attempt"

    /// Login success
    public static let loginSuccess = "login_success"

    /// Login failure
    public static let loginFailure = "login_failure"

    // ============================================================================
    // PAYMENT EVENTS
    // ============================================================================

    /// Payment process started
    public static let paymentStart = "payment_start"

    /// Payment completed successfully
    public static let paymentSuccess = "payment_success"

    /// Payment failed
    public static let paymentFailure = "payment_failure"

    // ============================================================================
    // FEATURE USAGE EVENTS
    // ============================================================================

    /// Journal entry created
    public static let journalEntryCreated = "journal_entry_created"

    /// Assessment started
    public static let assessmentStarted = "assessment_started"

    /// Assessment completed
    public static let assessmentCompleted = "assessment_completed"

    /// Report viewed
    public static let reportViewed = "report_viewed"

    // ============================================================================
    // SYSTEM EVENTS
    // ============================================================================

    /// App launched
    public static let appLaunch = "app_launch"

    /// App backgrounded
    public static let appBackground = "app_background"

    /// App foregrounded
    public static let appForeground = "app_foreground"

    /// App crashed
    public static let appCrash = "app_crash"

    /// Device rotated
    public static let deviceRotation = "device_rotation"

    // ============================================================================
    // SESSION EVENTS
    // ============================================================================

    /// Session started
    public static let sessionStart = "session_start"

    /// Session ended
    public static let sessionEnd = "session_end"

    // ============================================================================
    // ENGAGEMENT & BEHAVIOR EVENTS
    // ============================================================================

    /// 25% scroll depth reached
    public static let scrollDepth25 = "scroll_depth_25"

    /// 50% scroll depth reached
    public static let scrollDepth50 = "scroll_depth_50"

    /// 75% scroll depth reached
    public static let scrollDepth75 = "scroll_depth_75"

    /// 100% scroll depth reached
    public static let scrollDepth100 = "scroll_depth_100"

    // ============================================================================
    // SCREEN TIME TRACKING EVENTS
    // ============================================================================

    /// User entered a screen
    public static let screenEnter = "screen_enter"

    /// User exited a screen
    public static let screenExit = "screen_exit"

    // ============================================================================
    // ERROR EVENTS
    // ============================================================================

    /// Network error occurred
    public static let networkError = "network_error"

    /// API error occurred
    public static let apiError = "api_error"

    /// Validation error occurred
    public static let validationError = "validation_error"

    /// Client-side validation failed
    public static let validationFailed = "validation_failed"
}