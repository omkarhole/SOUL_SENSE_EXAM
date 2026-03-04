# Analytics Event Architecture & Standardization

This document outlines the standardized approach to analytics event tracking across all Soul Sense platforms (Web, iOS, Android, Desktop).

## 🎯 User Identity & Session Tracking

### Guest User Mode
- **Persistent Guest IDs**: Generated on first app launch, stored securely
- **Cross-Session Identity**: Same guest ID used until user authenticates
- **Seamless Transition**: Guest ID cleared upon successful login

### Session Management
- **Automatic Tracking**: Sessions start on app foreground, end on background
- **Duration Calculation**: Precise session length tracking
- **Crash Handling**: Sessions properly closed on app termination

### Implementation Details

#### Web (TypeScript)
```typescript
// Automatic session management
analytics.startSession(); // Called on page load/visibility
analytics.endSession();   // Called on page hide/unload

// User identity management
analytics.setUserId('user123'); // After login
analytics.clearUserId();        // After logout (back to guest)
```

#### Android (Java)
```java
// Initialize in Application class
AnalyticsManager analytics = AnalyticsManager.getInstance(context);

// Automatic session tracking via Activity lifecycle
analytics.startSession(); // onResume
analytics.endSession();   // onPause

// User management
analytics.setUserId("user123");
analytics.clearUserId();
```

#### iOS (Swift)
```swift
// Initialize in AppDelegate
let analytics = AnalyticsManager.shared()

// Automatic via UIApplication notifications
// Sessions start/end automatically

// User management
analytics.setUserId("user123")
analytics.clearUserId()
```

## � Scroll Depth Tracking

### Threshold Detection
- **25%**: First engagement milestone
- **50%**: Content consumption midpoint  
- **75%**: High engagement indicator
- **100%**: Complete content consumption

### Implementation
- **One-time firing**: Each threshold fires only once per page/screen
- **Throttled tracking**: 100ms debounce to prevent excessive events
- **Cross-platform**: Consistent behavior across web, Android, and iOS

### Web Implementation
```typescript
// Automatic scroll tracking with threshold detection
analytics.setupScrollDepthTracking();

// Manual tracking (if needed)
analytics.trackScrollDepth(75); // Fires scroll_depth_75 event
```

### Android Implementation
```java
// Track scroll depth in scroll listeners
analytics.trackScrollDepth(50, "article_screen");
```

### iOS Implementation
```swift
// Track scroll depth in scroll view delegates
analytics.trackScrollDepth(100, screenName: "profile_screen")
```

## 📊 Engagement & Behavior Events

### session_start
**Triggered**: App launch, foreground, or manual start
**Properties**: None
```json
{
  "event_name": "session_start",
  "user_id": "guest_1234567890_abc123def",
  "session_id": "session_1640995200000_xyz789",
  "platform": "web",
  "app_version": "1.0.0"
}
```

### session_end
**Triggered**: App background, termination, or manual end
**Properties**:
- `session_duration_ms`: Duration in milliseconds
- `session_duration_seconds`: Duration in seconds (rounded)
```json
{
  "event_name": "session_end",
  "user_id": "guest_1234567890_abc123def",
  "session_id": "session_1640995200000_xyz789",
  "platform": "web",
  "app_version": "1.0.0",
  "event_properties": {
    "session_duration_ms": 3600000,
    "session_duration_seconds": 3600
  }
}
```

### scroll_depth_25
**Triggered**: User scrolls to 25% of page/screen content
**Properties**:
- `scroll_percentage`: 25
- `page_url`: Current page URL (web)
- `screen_name`: Current screen name (mobile)
```json
{
  "event_name": "scroll_depth_25",
  "user_id": "guest_1234567890_abc123def",
  "session_id": "session_1640995200000_xyz789",
  "platform": "web",
  "app_version": "1.0.0",
  "event_properties": {
    "scroll_percentage": 25,
    "page_url": "https://soulsense.app/article/123"
  }
}
```

### scroll_depth_50
**Triggered**: User scrolls to 50% of page/screen content
**Properties**: Same as scroll_depth_25 with `scroll_percentage`: 50

### scroll_depth_75
**Triggered**: User scrolls to 75% of page/screen content
**Properties**: Same as scroll_depth_25 with `scroll_percentage`: 75

### scroll_depth_100
**Triggered**: User scrolls to 100% of page/screen content (bottom)
**Properties**: Same as scroll_depth_25 with `scroll_percentage`: 100

## 🔧 User Identity Flow

### Guest Mode
1. **First Launch**: Generate UUID, store persistently
2. **All Events**: Use guest ID as `user_id`
3. **Analytics**: Track user behavior before signup

### Authenticated Mode
1. **Login Success**: Call `setUserId(authenticatedUserId)`
2. **Guest Cleanup**: Remove stored guest ID
3. **All Events**: Use authenticated user ID

### Logout
1. **Logout Event**: Track logout action
2. **Identity Reset**: Call `clearUserId()`
3. **Guest Mode**: Return to guest identity

## ✅ Test Cases

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| AN-010 | Fresh install | UUID generated and stored |
| AN-011 | App restart | Same UUID reused |
| AN-012 | User login | Guest ID cleared, user ID set |
| AN-013 | User logout | Back to guest mode |
| AN-014 | App to background | session_end with duration |
| AN-015 | App to foreground | session_start triggered |
| AN-016 | App crash | Last session properly closed |
| AN-017 | Scroll to 25% | scroll_depth_25 event fired |
| AN-018 | Scroll to 50% | scroll_depth_50 event fired |
| AN-019 | Scroll to 75% | scroll_depth_75 event fired |
| AN-020 | Scroll to 100% | scroll_depth_100 event fired |
| AN-021 | Multiple scrolls | Each threshold fires only once |

## 🔒 Security & Privacy

### Guest ID Storage
- **Web**: localStorage (client-side only)
- **Android**: SharedPreferences (encrypted if available)
- **iOS**: UserDefaults (secure storage)

### Data Handling
- Guest IDs are anonymous, no PII
- Session data includes only technical metrics
- No sensitive user data in analytics events

## 📈 Benefits

### Analytics Quality
- **Complete User Journey**: Track from first visit to conversion
- **Accurate Sessions**: Proper session boundaries
- **User Attribution**: Consistent identity across sessions

### Business Intelligence
- **User Engagement**: Understand session patterns
- **Conversion Funnel**: Track guest to registered user flow
- **Retention Metrics**: Session duration and frequency

### Technical Reliability
- **Crash Recovery**: Sessions closed on unexpected termination
- **Cross-Platform**: Consistent behavior across all platforms
- **Performance**: Lightweight implementation

## 📋 Standards

### Event Naming Convention
- **Format**: `snake_case` (lowercase with underscores)
- **No spaces**: Use underscores instead of spaces
- **No camelCase**: `buttonClick` → `button_click`
- **No prefixes**: Avoid undocumented prefixes like `viewScreen`
- **Pattern**: `^[a-z][a-z0-9_]*$`

### Examples
```javascript
// ✅ Correct
screen_view
button_click
signup_start
payment_success

// ❌ Incorrect
screenView
Screen_View
viewScreen
button-click
```

## 🏗️ Implementation

### 1. Centralized Constants

#### Web (TypeScript)
Location: `frontend-web/src/lib/utils/analytics.ts`
```typescript
export const ANALYTICS_EVENTS = {
  SCREEN_VIEW: 'screen_view',
  BUTTON_CLICK: 'button_click',
  // ... all events
} as const;
```

#### Android (Java)
Location: `mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java`
```java
public final class AnalyticsEvents {
    public static final String SCREEN_VIEW = "screen_view";
    public static final String BUTTON_CLICK = "button_click";
    // ... all events
}
```

#### iOS (Swift)
Location: `mobile-app/ios/SoulSense/AnalyticsEvents.swift`
```swift
public final class AnalyticsEvents {
    public static let screenView = "screen_view"
    public static let buttonClick = "button_click"
    // ... all events
}
```

### 2. Event Schema

Location: `shared/analytics/event_schema.json`

The master schema defines:
- Required fields for all events
- Event-specific property validation
- Platform enumeration
- Schema versioning

### 3. Validation

#### Pre-commit Validation
Run validation before commits:
```bash
npm run validate:analytics  # Web
node scripts/validate_analytics.js  # Direct
```

#### CI/CD Validation
GitHub Actions workflow validates on PRs and pushes to main branches.

## 📊 Event Categories

### Screen View Events
- `screen_view` - Generic screen view
- `login_screen_view` - Login screen
- `signup_screen_view` - Signup screen
- `profile_screen_view` - Profile screen
- `settings_screen_view` - Settings screen

### User Interaction Events
- `button_click` - Generic button click
- `start_button_click` - Start button
- `login_button_click` - Login button
- `signup_button_click` - Signup button
- `logout_button_click` - Logout button

### Authentication Events
- `signup_start` - Signup process started
- `signup_success` - Signup completed
- `signup_failure` - Signup failed
- `login_attempt` - Login attempt
- `login_success` - Login success
- `login_failure` - Login failure

### Payment Events
- `payment_start` - Payment process started
- `payment_success` - Payment completed
- `payment_failure` - Payment failed

### Feature Usage Events
- `journal_entry_created` - Journal entry created
- `assessment_started` - Assessment started
- `assessment_completed` - Assessment completed
- `report_viewed` - Report viewed

### System Events
- `app_launch` - App launched
- `app_background` - App backgrounded
- `app_foreground` - App foregrounded
- `app_crash` - App crashed
- `device_rotation` - Device rotated

### Error Events
- `network_error` - Network error
- `api_error` - API error
- `validation_error` - Validation error

## 🔧 Usage Examples

### Web (TypeScript)
```typescript
import { analytics } from '@/lib/utils/analytics';

// Track screen view
analytics.trackPageView('/dashboard');

// Track button click
analytics.trackButtonClick('start-assessment', 'button');

// Track signup start
analytics.trackSignupStart('google', 'campaign_123');
```

### Android (Java)
```java
import com.soulsense.AnalyticsEvents;

// Track screen view
analytics.trackEvent(AnalyticsEvents.SCREEN_VIEW, properties);

// Track button click
analytics.trackEvent(AnalyticsEvents.BUTTON_CLICK, buttonProperties);
```

### iOS (Swift)
```swift
import SoulSense

// Track screen view
Analytics.track(event: AnalyticsEvents.screenView, properties: properties)

// Track button click
Analytics.track(event: AnalyticsEvents.buttonClick, properties: buttonProperties)
```

## ✅ Testing

### Test Cases

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| AN-001 | Open Home Screen | `screen_view` event |
| AN-002 | Click Start Button | `start_button_click` event |
| AN-003 | Rotate Device | No new event variant |
| AN-004 | Invalid event name | Validation failure |

### Validation Commands
```bash
# Validate all platforms
node scripts/validate_analytics.js

# Web-specific validation
npm run validate:analytics

# Run tests
pytest tests/test_analytics_standardization.py
```

## 🚨 Risk Mitigation

### Data Fragmentation Prevention
- **Pre-commit hooks**: Block commits with invalid event names
- **CI validation**: Fail builds with schema violations
- **Cross-platform sync**: Single source of truth for event constants

### Schema Drift Prevention
- **Version control**: Schema changes require version bumps
- **Validation**: Payload validation before sending
- **Documentation**: Clear guidelines for adding new events

## 📈 Monitoring

### Dashboards
- Monitor event consistency across platforms
- Alert on unknown event names
- Track schema compliance rates

### Metrics
- Event naming consistency score
- Schema validation pass rate
- Cross-platform event parity

## 🔄 Adding New Events

1. **Add to schema**: Update `shared/analytics/event_schema.json`
2. **Update constants**: Add to all platform constant files
3. **Validate**: Run validation scripts
4. **Test**: Add test cases
5. **Document**: Update this README

## 📞 Support

For questions about analytics standardization:
- Check this document first
- Run validation scripts for issues
- Create PR with schema changes for new events