#!/usr/bin/env python3
"""
Simple test script for Signed URL Policy Hardening
"""

import sys
import os

# Add the backend/fastapi directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend', 'fastapi')
sys.path.insert(0, backend_dir)

def test_signed_url_policy():
    """Basic functionality test for signed URL policy."""
    try:
        # Import only the storage_service module directly to avoid other service dependencies
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "storage_service",
            os.path.join(backend_dir, "api", "services", "storage_service.py")
        )
        storage_module = importlib.util.module_from_spec(spec)

        # Mock the dependencies that might cause issues
        import types
        mock_config = types.ModuleType('config')
        mock_get_settings_instance = lambda: types.SimpleNamespace(
            s3_region='us-east-1',
            aws_access_key_id=None,
            aws_secret_access_key=None
        )
        mock_config.get_settings_instance = mock_get_settings_instance
        sys.modules['api.config'] = mock_config

        # Execute the module but catch the global instantiation
        try:
            spec.loader.exec_module(storage_module)
        except NameError:
            # The global instance failed, but the class should still be available
            pass

        SignedURLPolicy = storage_module.SignedURLPolicy

        # Create policy with mock settings
        policy = SignedURLPolicy.__new__(SignedURLPolicy)
        policy.settings = mock_get_settings_instance()

        # Test expiration validation
        assert policy.validate_expiration(300) == 300
        assert policy.validate_expiration(7200) == 3600  # Clamped to max

        # Test method validation
        assert policy.validate_method('GET') == 'GET'
        try:
            policy.validate_method('POST')
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Test object path validation
        bucket, key = policy.validate_object_path('test-bucket', 'test-file.txt')
        assert bucket == 'test-bucket'
        assert key == 'test-file.txt'

        try:
            policy.validate_object_path('test-bucket', '../etc/passwd')
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Test IP validation
        assert policy.validate_ip_restriction('192.168.1.1') == '192.168.1.1'
        assert policy.validate_ip_restriction(None) is None

        print("✓ All SignedURLPolicy validation tests passed")

        # Test signed URL access validation (mock URL)
        test_url = "https://example.com/file?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=test&X-Amz-Signature=test"
        is_valid = policy.validate_signed_url_access(test_url)
        print(f"✓ Signed URL validation test: {is_valid}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_signed_url_policy()
    sys.exit(0 if success else 1)