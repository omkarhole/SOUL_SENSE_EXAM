#!/usr/bin/env python3
"""
Test script for Advanced Analytics and Emotional Pattern Recognition (Feature #804).

This script tests the new ML services and API endpoints.
"""

import sys
import os
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_session
from app.models import User, Score, JournalEntry
from app.ml.pattern_recognition import PatternRecognitionService
from app.ml.recommendation_engine import RecommendationEngine
from app.ml.analytics_service import AnalyticsService


def test_pattern_recognition():
    """Test the pattern recognition service."""
    print("Testing Pattern Recognition Service...")

    session = get_session()
    try:
        # Get a test user
        user = session.query(User).first()
        if not user:
            print("No users found in database. Skipping pattern recognition test.")
            return

        service = PatternRecognitionService()

        # Test temporal patterns
        patterns = service.detect_temporal_patterns(user.username)
        print(f"Detected {len(patterns.get('patterns', []))} temporal patterns")
        print(f"Analysis based on {patterns.get('data_points', 0)} data points")

        # Test correlations
        correlations = service.find_correlations(user.username)
        print(f"Found {len(correlations.get('significant_correlations', []))} significant correlations")

        # Test triggers
        triggers = service.identify_triggers(user.username)
        print(f"Identified {len(triggers.get('triggers', []))} emotional triggers")

        # Test mood prediction
        forecast = service.predict_mood(user.username)
        print(f"Generated {len(forecast.get('predictions', []))} day mood forecast")

        print("✓ Pattern Recognition Service tests passed")

    except Exception as e:
        print(f"✗ Pattern Recognition Service test failed: {e}")
    finally:
        session.close()


def test_recommendation_engine():
    """Test the recommendation engine."""
    print("\nTesting Recommendation Engine...")

    session = get_session()
    try:
        # Get a test user
        user = session.query(User).first()
        if not user:
            print("No users found in database. Skipping recommendation engine test.")
            return

        engine = RecommendationEngine()

        # Test insights generation
        insights = engine.generate_insights(user.username)
        print(f"Generated {len(insights.get('insights', []))} personalized insights")

        # Test interventions
        interventions = engine.suggest_interventions(user.username)
        print(f"Suggested {len(interventions.get('interventions', []))} interventions")
        print(f"Risk level: {interventions.get('risk_level', 'unknown')}")

        # Test personalized prompts
        patterns = []  # Empty patterns for basic test
        prompts = engine.create_personalized_prompts(user.username, patterns)
        print(f"Created {len(prompts)} personalized journal prompts")

        print("✓ Recommendation Engine tests passed")

    except Exception as e:
        print(f"✗ Recommendation Engine test failed: {e}")
    finally:
        session.close()


def test_analytics_service():
    """Test the comprehensive analytics service."""
    print("\nTesting Analytics Service...")

    session = get_session()
    try:
        # Get a test user
        user = session.query(User).first()
        if not user:
            print("No users found in database. Skipping analytics service test.")
            return

        service = AnalyticsService()

        # Test emotional forecast
        forecast = service.get_emotional_forecast(user.username)
        print(f"Generated emotional forecast with {len(forecast.get('forecast', {}).get('predictions', []))} predictions")

        # Test correlation matrix
        correlations = service.get_correlation_matrix(user.username)
        print(f"Generated correlation analysis with {len(correlations.get('significant_correlations', []))} significant correlations")

        # Test personalized recommendations
        recommendations = service.get_personalized_recommendations(user.username)
        print(f"Generated {len(recommendations.get('insights', {}).get('insights', []))} insights and {len(recommendations.get('interventions', {}).get('interventions', []))} interventions")

        # Test analytics dashboard
        dashboard = service.get_analytics_dashboard(user.username)
        print("Generated complete analytics dashboard")

        print("✓ Analytics Service tests passed")

    except Exception as e:
        print(f"✗ Analytics Service test failed: {e}")
    finally:
        session.close()


def test_database_models():
    """Test the new database models."""
    print("\nTesting Database Models...")

    from app.models import EmotionalPattern, UserBenchmark, AnalyticsInsight, MoodForecast

    session = get_session()
    try:
        # Test creating records
        test_pattern = EmotionalPattern(
            username="test_user",
            pattern_type="temporal",
            pattern_data=json.dumps({"test": "data"}),
            confidence_score=0.8
        )
        session.add(test_pattern)

        test_benchmark = UserBenchmark(
            username="test_user",
            benchmark_type="overall",
            percentile=75,
            comparison_group="all_users",
            benchmark_data=json.dumps({"test": "benchmark"})
        )
        session.add(test_benchmark)

        test_insight = AnalyticsInsight(
            username="test_user",
            insight_type="pattern",
            category="temporal",
            title="Test Insight",
            description="Test description",
            recommendation="Test recommendation",
            confidence=0.7,
            priority="medium"
        )
        session.add(test_insight)

        test_forecast = MoodForecast(
            username="test_user",
            forecast_date=datetime.now(),
            predicted_score=75.5,
            confidence=0.8,
            forecast_basis=json.dumps({"test": "basis"})
        )
        session.add(test_forecast)

        session.commit()
        print("✓ Successfully created test records in new tables")

        # Clean up test records
        session.delete(test_forecast)
        session.delete(test_insight)
        session.delete(test_benchmark)
        session.delete(test_pattern)
        session.commit()
        print("✓ Successfully cleaned up test records")

        print("✓ Database Models tests passed")

    except Exception as e:
        print(f"✗ Database Models test failed: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    """Run all tests."""
    print("🧠 Advanced Analytics and Emotional Pattern Recognition - Test Suite")
    print("=" * 70)

    # Test individual components
    test_database_models()
    test_pattern_recognition()
    test_recommendation_engine()
    test_analytics_service()

    print("\n" + "=" * 70)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Run the analytics pipeline: python scripts/analytics_pipeline.py")
    print("2. Test the API endpoints with authentication")
    print("3. Review generated insights and patterns")


if __name__ == "__main__":
    main()