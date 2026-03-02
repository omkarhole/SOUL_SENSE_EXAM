"""
Test cases for Analytics Event Standardization
Tests the validation of event naming conventions and schema compliance.
"""

import unittest
import json
import os


class TestAnalyticsStandardization(unittest.TestCase):

    def setUp(self):
        self.schema_path = os.path.join(os.path.dirname(__file__), '../shared/analytics/event_schema.json')
        with open(self.schema_path) as f:
            self.schema = json.load(f)

    def test_event_name_format(self):
        """Test that all event names follow snake_case convention."""
        allowed_events = self.schema['properties']['event_name']['enum']

        for event in allowed_events:
            with self.subTest(event=event):
                # Should be lowercase, snake_case
                self.assertTrue(event.islower(), f"Event '{event}' is not lowercase")
                self.assertNotIn(' ', event, f"Event '{event}' contains spaces")
                self.assertNotIn('-', event, f"Event '{event}' contains hyphens")
                # Should not contain uppercase
                self.assertEqual(event, event.lower(), f"Event '{event}' contains uppercase")

    def test_no_duplicate_events(self):
        """Test that there are no duplicate event names in schema."""
        allowed_events = self.schema['properties']['event_name']['enum']
        unique_events = set(allowed_events)
        self.assertEqual(len(allowed_events), len(unique_events), "Duplicate events found in schema")

    def test_schema_version_exists(self):
        """Test that schema has a version field."""
        self.assertIn('version', self.schema, "Schema missing version field")
        self.assertEqual(self.schema['version'], '1.0', "Schema version should be 1.0")

    def test_required_fields(self):
        """Test that schema defines required fields."""
        required = self.schema.get('required', [])
        expected_required = ['event_name', 'timestamp', 'session_id', 'platform', 'app_version']
        for field in expected_required:
            with self.subTest(field=field):
                self.assertIn(field, required, f"Required field '{field}' missing from schema")

    def test_event_properties_schema(self):
        """Test that event_properties has proper validation."""
        event_props = self.schema['properties']['event_properties']
        self.assertIn('oneOf', event_props, "event_properties should have oneOf validation")

        # Should have different property sets for different event types
        one_of_options = event_props['oneOf']
        self.assertGreater(len(one_of_options), 1, "Should have multiple property validation options")

    def test_platform_enum(self):
        """Test that platform field has correct enum values."""
        platform_enum = self.schema['properties']['platform']['enum']
        expected_platforms = ['ios', 'android', 'web', 'desktop']
        self.assertEqual(set(platform_enum), set(expected_platforms), "Platform enum mismatch")

    def test_session_events_in_schema(self):
        """Test that session events are included in schema."""
        allowed_events = self.schema['properties']['event_name']['enum']
        
        session_events = ['session_start', 'session_end']
        for event in session_events:
            with self.subTest(event=event):
                self.assertIn(event, allowed_events, f"Session event '{event}' not in schema")

    def test_session_end_properties_schema(self):
        """Test that session_end event properties are properly defined."""
        event_props = self.schema['properties']['event_properties']['oneOf']
        
        # Find the session duration properties
        session_props = None
        for option in event_props:
            if 'session_duration_ms' in option.get('properties', {}):
                session_props = option
                break
        
        self.assertIsNotNone(session_props, "Session duration properties not found in schema")
        self.assertIn('session_duration_seconds', session_props['properties'], 
                     "session_duration_seconds property missing")

    def test_guest_user_id_persistence(self):
        """Test that guest user ID concept is supported in schema."""
        # The schema should allow user_id to be optional (for guest users)
        user_id_field = self.schema['properties']['user_id']
        self.assertIn('null', user_id_field.get('type', []), 
                     "Schema should allow null user_id for guest users")

    def test_session_id_required(self):
        """Test that session_id is required."""
        required_fields = self.schema.get('required', [])
        self.assertIn('session_id', required_fields, "session_id should be required")