#!/usr/bin/env python3
"""
Daily Analytics Pipeline for Advanced Emotional Pattern Recognition.

This script runs daily analytics processing for all active users:
- Detects temporal patterns
- Finds correlations
- Generates insights and recommendations
- Updates forecasts
- Maintains benchmark data

Usage:
    python scripts/analytics_pipeline.py [--dry-run] [--user USERNAME] [--force]

Options:
    --dry-run: Show what would be processed without making changes
    --user USERNAME: Process only specific user
    --force: Force reprocessing of recent data
"""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional
import argparse

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_session
from app.models import User, EmotionalPattern, UserBenchmark, AnalyticsInsight, MoodForecast
from app.ml.analytics_service import AnalyticsService
from app.ml.pattern_recognition import PatternRecognitionService
from app.ml.recommendation_engine import RecommendationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analytics_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AnalyticsPipeline:
    """Daily analytics processing pipeline."""

    def __init__(self, dry_run: bool = False):
        """Initialize the analytics pipeline."""
        self.dry_run = dry_run
        self.session = get_session()
        self.analytics_service = AnalyticsService()
        self.pattern_service = PatternRecognitionService()
        self.recommendation_engine = RecommendationEngine()

    def run_daily_pipeline(self, target_user: Optional[str] = None, force: bool = False):
        """
        Run the complete daily analytics pipeline.

        Args:
            target_user: Optional specific user to process
            force: Force reprocessing even if recently done
        """
        logger.info("Starting daily analytics pipeline...")

        try:
            # Get active users
            users = self._get_active_users(target_user)

            total_processed = 0
            total_errors = 0

            for user in users:
                try:
                    logger.info(f"Processing analytics for user: {user.username}")

                    # Check if we should skip (recently processed and not forced)
                    if not force and self._recently_processed(user.username):
                        logger.info(f"Skipping {user.username} - recently processed")
                        continue

                    # Process user analytics
                    self._process_user_analytics(user.username)

                    total_processed += 1

                except Exception as e:
                    logger.error(f"Error processing user {user.username}: {e}")
                    total_errors += 1
                    continue

            logger.info(f"Pipeline completed. Processed: {total_processed}, Errors: {total_errors}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            self.session.close()

    def _get_active_users(self, target_user: Optional[str] = None) -> List[User]:
        """Get active users for processing."""
        query = self.session.query(User).filter(User.is_active == True)

        if target_user:
            query = query.filter(User.username == target_user)

        # Only process users with recent activity (last 90 days)
        ninety_days_ago = datetime.now() - timedelta(days=90)
        query = query.filter(User.last_activity >= ninety_days_ago.isoformat())

        return query.all()

    def _recently_processed(self, username: str, hours: int = 24) -> bool:
        """Check if user was recently processed."""
        cutoff = datetime.now() - timedelta(hours=hours)

        # Check recent patterns
        recent_pattern = self.session.query(EmotionalPattern).filter(
            EmotionalPattern.username == username,
            EmotionalPattern.detected_at >= cutoff
        ).first()

        return recent_pattern is not None

    def _process_user_analytics(self, username: str):
        """Process all analytics for a single user."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would process analytics for {username}")
            return

        # 1. Detect and store patterns
        self._update_patterns(username)

        # 2. Update correlations (stored in pattern data)
        self._update_correlations(username)

        # 3. Generate and store insights
        self._update_insights(username)

        # 4. Update forecasts
        self._update_forecasts(username)

        # 5. Update benchmarks
        self._update_benchmarks(username)

        logger.info(f"Completed analytics processing for {username}")

    def _update_patterns(self, username: str):
        """Detect and store emotional patterns."""
        patterns_data = self.pattern_service.detect_temporal_patterns(username)

        for pattern in patterns_data.get("patterns", []):
            # Check if pattern already exists
            existing = self.session.query(EmotionalPattern).filter(
                EmotionalPattern.username == username,
                EmotionalPattern.pattern_type == pattern.get("type"),
                EmotionalPattern.detected_at >= datetime.now() - timedelta(hours=24)
            ).first()

            if existing:
                # Update existing
                existing.pattern_data = json.dumps(pattern)
                existing.confidence_score = pattern.get("confidence", 0.0)
                existing.last_updated = datetime.now()
            else:
                # Create new
                new_pattern = EmotionalPattern(
                    username=username,
                    pattern_type=pattern.get("type"),
                    pattern_data=json.dumps(pattern),
                    confidence_score=pattern.get("confidence", 0.0)
                )
                self.session.add(new_pattern)

        self.session.commit()

    def _update_correlations(self, username: str):
        """Update correlation analysis."""
        correlations = self.pattern_service.find_correlations(username)

        # Store as a special pattern type
        correlation_pattern = {
            "type": "correlation",
            "correlations": correlations,
            "generated_at": datetime.now().isoformat()
        }

        existing = self.session.query(EmotionalPattern).filter(
            EmotionalPattern.username == username,
            EmotionalPattern.pattern_type == "correlation"
        ).first()

        if existing:
            existing.pattern_data = json.dumps(correlation_pattern)
            existing.last_updated = datetime.now()
        else:
            new_pattern = EmotionalPattern(
                username=username,
                pattern_type="correlation",
                pattern_data=json.dumps(correlation_pattern),
                confidence_score=0.8  # Correlation analysis confidence
            )
            self.session.add(new_pattern)

        self.session.commit()

    def _update_insights(self, username: str):
        """Generate and store personalized insights."""
        insights_data = self.recommendation_engine.generate_insights(username)

        for insight in insights_data.get("insights", []):
            # Check for duplicate recent insights
            existing = self.session.query(AnalyticsInsight).filter(
                AnalyticsInsight.username == username,
                AnalyticsInsight.title == insight.get("title"),
                AnalyticsInsight.created_at >= datetime.now() - timedelta(days=7)
            ).first()

            if not existing:
                new_insight = AnalyticsInsight(
                    username=username,
                    insight_type=insight.get("type", "general"),
                    category=insight.get("category", "general"),
                    title=insight.get("title", ""),
                    description=insight.get("description", ""),
                    recommendation=insight.get("recommendation"),
                    confidence=insight.get("confidence", 0.5),
                    priority=insight.get("priority", "medium"),
                    insight_data=json.dumps(insight)
                )
                self.session.add(new_insight)

        self.session.commit()

    def _update_forecasts(self, username: str):
        """Update mood forecasts."""
        forecast_data = self.analytics_service.get_emotional_forecast(username)

        # Clear old forecasts
        self.session.query(MoodForecast).filter(
            MoodForecast.username == username,
            MoodForecast.forecast_date >= datetime.now().date()
        ).delete()

        # Add new forecasts
        for prediction in forecast_data.get("forecast", {}).get("predictions", []):
            forecast_date = datetime.fromisoformat(prediction["date"])
            new_forecast = MoodForecast(
                username=username,
                forecast_date=forecast_date,
                predicted_score=prediction["predicted_score"],
                confidence=prediction.get("confidence", 0.5),
                forecast_basis=json.dumps(forecast_data.get("patterns", {}))
            )
            self.session.add(new_forecast)

        self.session.commit()

    def _update_benchmarks(self, username: str):
        """Update user benchmarks."""
        benchmarks_data = self.analytics_service.get_comparative_benchmarks(username)

        # Store benchmark data
        benchmark_info = benchmarks_data.get("benchmarks", {})

        existing = self.session.query(UserBenchmark).filter(
            UserBenchmark.username == username,
            UserBenchmark.benchmark_type == "overall"
        ).first()

        if existing:
            existing.percentile = benchmark_info.get("user_percentile", 50)
            existing.benchmark_data = json.dumps(benchmarks_data)
        else:
            new_benchmark = UserBenchmark(
                username=username,
                benchmark_type="overall",
                percentile=benchmark_info.get("user_percentile", 50),
                comparison_group=benchmark_info.get("comparison_group", "all_users"),
                benchmark_data=json.dumps(benchmarks_data)
            )
            self.session.add(new_benchmark)

        self.session.commit()


def main():
    """Main entry point for the analytics pipeline."""
    parser = argparse.ArgumentParser(description="Daily Analytics Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without making changes")
    parser.add_argument("--user", type=str, help="Process only specific user")
    parser.add_argument("--force", action="store_true", help="Force reprocessing of recent data")

    args = parser.parse_args()

    try:
        pipeline = AnalyticsPipeline(dry_run=args.dry_run)
        pipeline.run_daily_pipeline(target_user=args.user, force=args.force)

        if args.dry_run:
            logger.info("Dry run completed successfully")
        else:
            logger.info("Analytics pipeline completed successfully")

    except Exception as e:
        logger.error(f"Analytics pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()