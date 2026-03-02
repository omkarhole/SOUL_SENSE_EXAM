#!/usr/bin/env python3
"""
Analytics Comprehensive Test Suite
Tests for issue #978 - QA & Testing Deficiencies

This test suite validates:
- Screen time tracking accuracy
- Error logging functionality
- Cross-platform consistency
- Schema validation
- Environment separation
"""

import unittest
import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile

class AnalyticsTestSuite(unittest.TestCase):
    """Comprehensive analytics testing suite"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.shared_analytics = self.project_root / "shared" / "analytics"
        self.schema_path = self.shared_analytics / "event_schema.json"

        # Load schema
        with open(self.schema_path, 'r') as f:
            self.schema = json.load(f)

    def test_schema_validity(self):
        """Test that the event schema is valid JSON and has required structure"""
        # Test JSON validity
        self.assertIsInstance(self.schema, dict)

        # Test required fields
        required_fields = ['properties', 'required', 'additionalProperties']
        for field in required_fields:
            self.assertIn(field, self.schema, f"Schema missing required field: {field}")

        # Test event_name enum exists
        self.assertIn('event_name', self.schema['properties'])
        self.assertIn('enum', self.schema['properties']['event_name'])
        self.assertIsInstance(self.schema['properties']['event_name']['enum'], list)

        # Test event_properties oneOf structure
        self.assertIn('event_properties', self.schema['properties'])
        self.assertIn('oneOf', self.schema['properties']['event_properties'])
        self.assertIsInstance(self.schema['properties']['event_properties']['oneOf'], list)

    def test_top_20_events_present(self):
        """Test that all top 20 critical events are defined in schema"""
        top_20_events = [
            'screen_view', 'session_start', 'session_end', 'button_click',
            'login_success', 'signup_success', 'app_launch', 'api_error',
            'validation_failed', 'screen_enter', 'screen_exit', 'scroll_depth_25',
            'scroll_depth_50', 'scroll_depth_75', 'scroll_depth_100',
            'logout_button_click', 'assessment_started', 'assessment_completed',
            'report_viewed', 'journal_entry_created'
        ]

        allowed_events = self.schema['properties']['event_name']['enum']

        for event in top_20_events:
            self.assertIn(event, allowed_events, f"Missing top 20 event: {event}")

    def test_no_duplicate_events(self):
        """Test that there are no duplicate events in the schema"""
        events = self.schema['properties']['event_name']['enum']
        unique_events = set(events)
        self.assertEqual(len(events), len(unique_events), "Duplicate events found in schema")

    def test_event_naming_convention(self):
        """Test that all events follow snake_case naming convention"""
        import re
        pattern = re.compile(r'^[a-z][a-z0-9_]*$')

        events = self.schema['properties']['event_name']['enum']
        for event in events:
            self.assertRegex(event, pattern, f"Event name doesn't follow snake_case: {event}")

    def test_web_analytics_constants(self):
        """Test that web analytics constants are properly defined"""
        web_analytics_path = self.project_root / "frontend-web" / "src" / "lib" / "utils" / "analytics.ts"

        if not web_analytics_path.exists():
            self.skipTest("Web analytics file not found")

        with open(web_analytics_path, 'r') as f:
            content = f.read()

        # Check for ANALYTICS_EVENTS constant
        self.assertIn('ANALYTICS_EVENTS', content, "ANALYTICS_EVENTS constant not found")

        # Check for screen time tracking methods
        self.assertIn('enterScreen', content, "enterScreen method not found")
        self.assertIn('exitScreen', content, "exitScreen method not found")

        # Check for error tracking methods
        self.assertIn('trackApiError', content, "trackApiError method not found")
        self.assertIn('trackValidationFailure', content, "trackValidationFailure method not found")

    def test_android_analytics_constants(self):
        """Test that Android analytics constants are properly defined"""
        android_events_path = self.project_root / "mobile-app" / "android" / "app" / "src" / "main" / "java" / "com" / "soulsense" / "AnalyticsEvents.java"

        if not android_events_path.exists():
            self.skipTest("Android analytics events file not found")

        with open(android_events_path, 'r') as f:
            content = f.read()

        # Check for top 20 events
        top_events = ['SCREEN_VIEW', 'SESSION_START', 'API_ERROR', 'VALIDATION_FAILED']
        for event in top_events:
            self.assertIn(event, content, f"Android constant not found: {event}")

    def test_ios_analytics_constants(self):
        """Test that iOS analytics constants are properly defined"""
        ios_events_path = self.project_root / "mobile-app" / "ios" / "SoulSense" / "AnalyticsEvents.swift"

        if not ios_events_path.exists():
            self.skipTest("iOS analytics events file not found")

        with open(ios_events_path, 'r') as f:
            content = f.read()

        # Check for top 20 events
        top_events = ['screenView', 'sessionStart', 'apiError', 'validationFailed']
        for event in top_events:
            self.assertIn(event, content, f"iOS constant not found: {event}")

    def test_validation_script_exists(self):
        """Test that the validation script exists and is executable"""
        validation_script = self.project_root / "scripts" / "validate_analytics.js"
        self.assertTrue(validation_script.exists(), "Validation script not found")

        # Test that it's executable (basic syntax check)
        try:
            result = subprocess.run(
                ['node', '--check', str(validation_script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0, f"Script syntax error: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("Script syntax check timed out")
        except FileNotFoundError:
            self.skipTest("Node.js not available for syntax check")

    def test_qa_checklist_generation(self):
        """Test that QA checklist can be generated"""
        checklist_path = self.project_root / "docs" / "ANALYTICS_QA_CHECKLIST.md"

        # Checklist should exist (created during setup)
        self.assertTrue(checklist_path.exists(), "QA checklist not found")

        with open(checklist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required sections
        required_sections = [
            "Top 20 Events Verification",
            "Schema Validation",
            "Cross-Platform Consistency",
            "Environment Separation"
        ]

        for section in required_sections:
            self.assertIn(section, content, f"QA checklist missing section: {section}")

    def test_environment_separation_config(self):
        """Test that environment-specific configurations exist"""
        env_files = [
            self.project_root / "frontend-web" / ".env.example",
            self.project_root / "frontend-web" / ".env.local",  # May not exist in CI
        ]

        # At least one environment file should exist
        env_exists = any(f.exists() for f in env_files)
        if not env_exists:
            self.skipTest("No environment files found")

        # Check that existing env files mention analytics or environment
        for env_file in env_files:
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
                    # Should have some environment or analytics configuration
                    has_config = 'ANALYTICS' in content or 'ENV' in content or 'environment' in content.lower()
                    if has_config:
                        break
        else:
            self.fail("No environment-specific analytics configuration found")

    def test_screen_time_event_properties(self):
        """Test that screen time events have proper properties defined"""
        # Find screen time related events in schema
        screen_events = ['screen_enter', 'screen_exit']
        event_properties = self.schema['properties']['event_properties']['oneOf']

        screen_time_found = False
        for prop_set in event_properties:
            if 'properties' in prop_set:
                props = prop_set['properties']
                if 'screen_name' in props and 'duration_ms' in props:
                    screen_time_found = True
                    # Validate property types
                    self.assertEqual(props['screen_name']['type'], 'string')
                    self.assertEqual(props['duration_ms']['type'], 'number')  # Schema uses 'number' for duration_ms
                    break

        self.assertTrue(screen_time_found, "Screen time event properties not properly defined")

    def test_error_event_properties(self):
        """Test that error events have proper properties defined"""
        # Find error related events in schema
        error_events = ['api_error', 'validation_failed']
        event_properties = self.schema['properties']['event_properties']['oneOf']

        api_error_found = False
        validation_error_found = False

        for prop_set in event_properties:
            if 'properties' in prop_set:
                props = prop_set['properties']
                if 'endpoint' in props and 'response_code' in props and 'latency' in props:
                    api_error_found = True
                if 'field_name' in props and 'reason' in props and 'validation_failed' in props:
                    validation_error_found = True

        self.assertTrue(api_error_found, "API error event properties not properly defined")
        self.assertTrue(validation_error_found, "Validation error event properties not properly defined")

    def test_cross_platform_consistency(self):
        """Test that event constants are consistent across platforms"""
        # This is a basic check - in practice, would need more sophisticated parsing
        platforms = {
            'web': self.project_root / "frontend-web" / "src" / "lib" / "utils" / "analytics.ts",
            'android': self.project_root / "mobile-app" / "android" / "app" / "src" / "main" / "java" / "com" / "soulsense" / "AnalyticsEvents.java",
            'ios': self.project_root / "mobile-app" / "ios" / "SoulSense" / "AnalyticsEvents.swift"
        }

        platform_events = {}

        for platform, path in platforms.items():
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                    # Extract event names (simplified - real implementation would be more robust)
                    if platform == 'web':
                        import re
                        matches = re.findall(r"'([a-z_]+)': '([a-z_]+)'", content)
                        platform_events[platform] = [match[1] for match in matches]
                    elif platform == 'android':
                        matches = re.findall(r'"([a-z_]+)"', content)
                        platform_events[platform] = list(set(matches))  # Remove duplicates
                    elif platform == 'ios':
                        matches = re.findall(r'"([a-z_]+)"', content)
                        platform_events[platform] = list(set(matches))  # Remove duplicates

        # Check that common events exist across platforms
        common_events = ['screen_view', 'session_start', 'api_error']
        for event in common_events:
            platforms_with_event = [p for p, events in platform_events.items() if event in events]
            # At least one platform should have each event
            self.assertGreater(len(platforms_with_event), 0, f"Event '{event}' not found in any platform")


if __name__ == '__main__':
    # Add project root to Python path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AnalyticsTestSuite)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)