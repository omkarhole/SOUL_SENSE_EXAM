import asyncio
import logging
from typing import Any, Dict, Callable, Awaitable

logger = logging.getLogger("api.utils.singleflight")

class SingleflightService:
    """
    Prevents "Thundering Herd" by collapsing multiple concurrent requests 
    for the same key into a single execution.
    """
    def __init__(self):
        self._inflight: Dict[str, asyncio.Future] = {}

    async def execute(self, key: str, func: Callable[[], Awaitable[Any]]) -> Any:
        """
        If a request for 'key' is already running, wait for it.
        Otherwise, start the execution and store the future.
        """
        if key in self._inflight:
            logger.debug(f"[Singleflight] Request collapsed for key: {key}")
            return await self._inflight[key]

        # Create a new future for this key
        future = asyncio.Future()
        self._inflight[key] = future

        try:
            # Execute the actual work
            result = await func()
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise e
        finally:
            # Always clean up so subsequent requests can re-run if needed
            if key in self._inflight:
                del self._inflight[key]

singleflight_service = SingleflightService()
