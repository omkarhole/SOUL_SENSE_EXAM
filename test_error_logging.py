#!/usr/bin/env python3
"""
Test script for error and crash logging implementation
Validates that API error tracking and validation failure logging work across all platforms
"""

import json
import os
import sys
from pathlib import Path

def test_event_schema():
    """Test that event schema includes error logging events"""
    schema_path = Path("shared/analytics/event_schema.json")
    if not schema_path.exists():
        print("❌ Event schema file not found")
        return False

    with open(schema_path, 'r') as f:
        schema = json.load(f)

    # Check for validation_failed in enum
    event_enum = schema.get('properties', {}).get('event_name', {}).get('enum', [])
    if 'validation_failed' not in event_enum:
        print("❌ Missing validation_failed in event enum")
        return False

    # Check for API error and validation failure properties in oneOf
    event_properties = schema.get('properties', {}).get('event_properties', {})
    one_of_options = event_properties.get('oneOf', [])

    # Look for API error properties (endpoint, response_code, error_message, latency, retry_count)
    api_error_found = False
    validation_failed_found = False

    for option in one_of_options:
        props = option.get('properties', {})
        if 'endpoint' in props and 'response_code' in props and 'latency' in props:
            api_error_found = True
        elif 'field_name' in props and 'reason' in props:
            validation_failed_found = True

    if not api_error_found:
        print("❌ Missing API error properties in schema")
        return False

    if not validation_failed_found:
        print("❌ Missing validation failed properties in schema")
        return False

    print("✅ Event schema validation passed")
    return True

def test_web_analytics():
    """Test web analytics implementation"""
    analytics_path = Path("frontend-web/src/lib/utils/analytics.ts")
    if not analytics_path.exists():
        print("❌ Web analytics file not found")
        return False

    with open(analytics_path, 'r') as f:
        content = f.read()

    # Check for error tracking methods
    required_methods = ['trackApiError', 'trackValidationFailure']
    for method in required_methods:
        if f'{method}(' not in content:
            print(f"❌ Missing method: {method} in web analytics")
            return False

    # Check for constants
    if 'API_ERROR' not in content or 'VALIDATION_FAILED' not in content:
        print("❌ Missing error tracking constants in web analytics")
        return False

    # Check for network interceptor setup
    if 'setupNetworkInterceptor' not in content:
        print("❌ Missing network interceptor setup in web analytics")
        return False

    print("✅ Web analytics implementation validated")
    return True

def test_android_analytics():
    """Test Android analytics implementation"""
    analytics_path = Path("mobile-app/android/app/src/main/java/com/soulsense/analytics/AnalyticsManager.java")
    interceptor_path = Path("mobile-app/android/app/src/main/java/com/soulsense/analytics/AnalyticsInterceptor.java")

    if not analytics_path.exists():
        print("❌ Android analytics file not found")
        return False

    if not interceptor_path.exists():
        print("❌ Android interceptor file not found")
        return False

    with open(analytics_path, 'r') as f:
        content = f.read()

    # Check for error tracking methods
    required_methods = ['trackApiError', 'trackValidationFailure']
    for method in required_methods:
        if f'public void {method}' not in content:
            print(f"❌ Missing method: {method} in Android analytics")
            return False

    # Check for getNetworkInterceptor method (different return type)
    if 'public AnalyticsInterceptor getNetworkInterceptor()' not in content:
        print("❌ Missing method: getNetworkInterceptor in Android analytics")
        return False

    print("✅ Android analytics implementation validated")
    return True

def test_ios_analytics():
    """Test iOS analytics implementation"""
    analytics_path = Path("mobile-app/ios/SoulSense/AnalyticsManager.swift")
    interceptor_path = Path("mobile-app/ios/SoulSense/AnalyticsNetworkInterceptor.swift")

    if not analytics_path.exists():
        print("❌ iOS analytics file not found")
        return False

    if not interceptor_path.exists():
        print("❌ iOS interceptor file not found")
        return False

    with open(analytics_path, 'r') as f:
        content = f.read()

    # Check for error tracking methods
    required_methods = ['trackApiError', 'trackValidationFailure', 'getNetworkInterceptor']
    for method in required_methods:
        if f'public func {method}' not in content:
            print(f"❌ Missing method: {method} in iOS analytics")
            return False

    print("✅ iOS analytics implementation validated")
    return True

def test_constants():
    """Test that constants are defined across platforms"""
    platforms = {
        'web': Path("frontend-web/src/lib/utils/analytics.ts"),
        'android': Path("mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java"),
        'ios': Path("mobile-app/ios/SoulSense/AnalyticsEvents.swift")
    }

    for platform, path in platforms.items():
        if not path.exists():
            print(f"❌ {platform.capitalize()} constants file not found")
            return False

        with open(path, 'r') as f:
            content = f.read()

        # Check for appropriate constants based on platform
        if platform == 'ios':
            if 'validationFailed' not in content:
                print(f"❌ Missing validation_failed constant in {platform}")
                return False
        else:
            if 'VALIDATION_FAILED' not in content:
                print(f"❌ Missing VALIDATION_FAILED constant in {platform}")
                return False

    print("✅ Constants validation passed across all platforms")
    return True

def main():
    """Run all validation tests"""
    print("🧪 Running error and crash logging implementation tests...\n")

    tests = [
        test_event_schema,
        test_web_analytics,
        test_android_analytics,
        test_ios_analytics,
        test_constants
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All error and crash logging implementations are valid!")
        return 0
    else:
        print("⚠️  Some implementations need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())