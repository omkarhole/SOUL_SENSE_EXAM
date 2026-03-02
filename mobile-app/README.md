# Mobile App

This directory contains the native mobile app implementations for iOS and Android.

## 📱 Platforms

### Android
- **Language**: Java
- **Location**: `android/`
- **Analytics Constants**: `android/app/src/main/java/com/soulsense/AnalyticsEvents.java`

### iOS
- **Language**: Swift
- **Location**: `ios/`
- **Analytics Constants**: `ios/SoulSense/AnalyticsEvents.swift`

## 📊 Analytics Standardization

All analytics events follow strict naming conventions defined in the [Analytics Architecture Documentation](../shared/analytics/README.md).

### Key Files
- **Event Schema**: `../shared/analytics/event_schema.json`
- **Validation Script**: `../scripts/validate_analytics.js`
- **Web Analytics**: `../frontend-web/src/lib/utils/analytics.ts`

### Validation
```bash
# Validate all platforms
node ../scripts/validate_analytics.js
```

## 🚀 Development

### Prerequisites
- Android Studio (for Android development)
- Xcode (for iOS development)
- Node.js (for validation scripts)

### Building
```bash
# Android
cd android
./gradlew build

# iOS
cd ios
xcodebuild -scheme SoulSense -sdk iphoneos -configuration Release
```

## 📋 Standards Compliance

- ✅ Event naming: snake_case only
- ✅ Schema validation: JSON Schema v7
- ✅ Cross-platform consistency
- ✅ Pre-commit validation
- ✅ CI/CD validation

See [Analytics README](../shared/analytics/README.md) for detailed standards.
flutter pub get
flutter run
```

## Structure

```
mobile-app/
├── lib/
│   ├── screens/         # Screen widgets
│   ├── widgets/         # Reusable widgets
│   ├── services/        # API, Auth, Notifications
│   └── models/          # Data models
└── pubspec.yaml
```

See `FILE_ARCHITECTURE.md` for detailed file mappings.
