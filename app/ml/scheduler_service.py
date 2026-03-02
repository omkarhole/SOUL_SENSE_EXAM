"""
Scheduler Service for Automated Analytics Processing.

Uses APScheduler to run daily analytics pipeline and background tasks.
Integrates with the analytics pipeline for automated processing.
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import asyncio

from app.ml.analytics_service import AnalyticsService
from app.db import safe_db_context
from app.models import User

logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """Scheduler for automated analytics processing."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            executors={
                'default': AsyncIOExecutor()
            },
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 30
            }
        )
        self._is_running = False

    def start(self):
        """Start the scheduler."""
        if not self._is_running:
            # Schedule daily analytics processing at 2 AM
            self.scheduler.add_job(
                func=self._run_daily_analytics,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_analytics',
                name='Daily Analytics Pipeline',
                replace_existing=True
            )

            # Schedule cache cleanup at 3 AM
            self.scheduler.add_job(
                func=self._cleanup_cache,
                trigger=CronTrigger(hour=3, minute=0),
                id='cache_cleanup',
                name='Cache Cleanup',
                replace_existing=True
            )

            self.scheduler.start()
            self._is_running = True
            logger.info("Analytics scheduler started successfully")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Analytics scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def run_daily_analytics_now(self) -> Dict[str, Any]:
        """Manually trigger daily analytics processing."""
        return asyncio.run(self._run_daily_analytics())

    async def _run_daily_analytics(self) -> Dict[str, Any]:
        """Run the daily analytics pipeline for all users."""
        logger.info("Starting daily analytics processing")

        try:
            with safe_db_context() as session:
                # Get all active users who have analytics enabled
                users = session.query(User).filter(
                    User.is_active == True,
                    User.is_deleted == False
                ).all()

                processed_users = 0
                failed_users = 0
                results = []

                for user in users:
                    try:
                        # Check if user has analytics enabled
                        if not user.settings or not user.settings.analytics_enabled:
                            continue

                        # Run analytics for this user
                        analytics_result = await self._process_user_analytics(user.username)
                        results.append({
                            "username": user.username,
                            "status": "success",
                            "patterns_found": len(analytics_result.get("patterns", [])),
                            "correlations_found": len(analytics_result.get("significant_correlations", []))
                        })
                        processed_users += 1

                    except Exception as e:
                        logger.error(f"Failed to process analytics for user {user.username}: {e}")
                        results.append({
                            "username": user.username,
                            "status": "failed",
                            "error": str(e)
                        })
                        failed_users += 1

                summary = {
                    "timestamp": datetime.now().isoformat(),
                    "total_users": len(users),
                    "processed_users": processed_users,
                    "failed_users": failed_users,
                    "results": results
                }

                logger.info(f"Daily analytics completed: {processed_users} processed, {failed_users} failed")
                return summary
        except Exception as e:
            logger.error(f"Daily analytics run failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _process_user_analytics(self, username: str) -> Dict[str, Any]:
        """Process analytics for a specific user."""
        service = AnalyticsService()

        # Detect patterns
        patterns = service.pattern_service.detect_temporal_patterns(username, "90d")

        # Find correlations
        correlations = service.get_correlation_matrix(username)

        # Generate forecast
        forecast = service.get_emotional_forecast(username, 7)

        # Generate recommendations
        recommendations = service.get_personalized_recommendations(username)

        # Store results in database (this would be implemented)
        # For now, just return the results
        return {
            "patterns": patterns,
            "correlations": correlations,
            "forecast": forecast,
            "recommendations": recommendations
        }

    async def _cleanup_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries."""
        try:
            # This would integrate with the cache service to clean up expired entries
            # For now, just log that cleanup would happen
            logger.info("Cache cleanup completed (placeholder)")
            return {"status": "completed", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


# Global scheduler instance
_scheduler = None

def get_scheduler() -> AnalyticsScheduler:
    """Get global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AnalyticsScheduler()
    return _scheduler
