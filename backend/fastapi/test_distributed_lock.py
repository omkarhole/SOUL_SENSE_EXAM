import asyncio
import logging
import sys
import os

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.utils.distributed_lock import require_lock

class MockRedis:
    def __init__(self):
        self._locks = {}
        self._lock = asyncio.Lock()

    async def set(self, key, value, nx=False, px=None):
        async with self._lock:
            if nx and key in self._locks:
                return None  # Lock already exists
            self._locks[key] = value
            return True

    async def eval(self, script, numkeys, *args):
        async with self._lock:
            key = args[0]
            val = args[1]
            if self._locks.get(key) == val:
                del self._locks[key]
                return 1
            return 0

mock_redis = MockRedis()

# Monkey patch get_redis for the test
from api.utils import distributed_lock
async def mock_get_redis():
    return mock_redis
distributed_lock.get_redis = mock_get_redis

class DummyUser:
    def __init__(self, id):
        self.id = id

class DummyService:
    @classmethod
    @require_lock(name="export_v2_{user.id}_{format}", timeout=10)
    async def generate_export(cls, user, format):
        logger.info(f"Worker started generating {format} export for user {user.id}...")
        # Simulate heavy work like generating a PDF
        await asyncio.sleep(3)
        logger.info(f"Worker finished generating {format} export for user {user.id}")
        return True

async def simulate_concurrent_requests():
    logger.info("Initializing Redis for lock testing...")

    
    user = DummyUser(id=42)
    format = "pdf"
    
    logger.info(f"Simulating 5 simultaneous clicks from User {user.id} for a {format} export")
    
    async def request_task(task_id):
        logger.info(f"[Request {task_id}] Attempting to generate export...")
        try:
            await DummyService.generate_export(user, format)
            logger.info(f"[Request {task_id}] SUCCESS: Export generated.")
        except RuntimeError as e:
            logger.error(f"[Request {task_id}] FAILED: {e}")

    # Launch 5 concurrent tasks
    tasks = [request_task(i) for i in range(1, 6)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(simulate_concurrent_requests())
