import asyncio
import os
import sys
import json

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

async def mock_test():
    from api.services.feature_flags import get_feature_service
    
    # Mock Consul client to avoid network errors
    class MockKV:
        def __init__(self):
            self.store = {
                "soulsense/features/new_dashboard": json.dumps({
                    "enabled": True,
                    "rollout_percentage": 50,
                    "tenant_overrides": {"99": False}
                })
            }
        def get(self, prefix, recurse=False):
            return 1, [{'Key': k, 'Value': v} for k, v in self.store.items()]
    
    class MockConsul:
        def __init__(self, **kwargs):
            self.kv = MockKV()

    import consul
    consul.Consul = MockConsul
    
    service = get_feature_service()
    
    # Case 1: Global Enabled
    print(f"Global: {service.is_enabled('new_dashboard')}") # True
    
    # Case 2: Tenant Override
    print(f"Tenant 99 override (False): {service.is_enabled('new_dashboard', tenant_id='99')}")
    
    # Case 3: Rollout check
    # user_id 1 hash should be different from user_id 2
    u1 = service.is_enabled('new_dashboard', user_id=1)
    u2 = service.is_enabled('new_dashboard', user_id=2)
    print(f"Rollout u1: {u1}, u2: {u2}")

if __name__ == "__main__":
    asyncio.run(mock_test())
