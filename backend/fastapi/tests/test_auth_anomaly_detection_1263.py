"""
Test Auth Anomaly Detection #1263
==================================

Comprehensive tests for authentication anomaly detection and risk scoring.
Tests baseline rules, enforcement actions, and false positive validation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from ..services.auth_anomaly_service import (
    AuthAnomalyService,
    AnomalyType,
    RiskLevel,
    EnforcementAction,
    RiskScore,
    GeoLocation
)
from ..models import AuthAnomalyEvent, LoginAttempt, UserSession


class TestAuthAnomalyService:
    """Test suite for AuthAnomalyService"""

    @pytest.fixture
    async def anomaly_service(self, db_session):
        """Create AuthAnomalyService instance with test database"""
        return AuthAnomalyService(db_session)

    @pytest.fixture
    async def sample_user(self, db_session):
        """Create a sample user for testing"""
        from ..models import User
        user = User(
            username="testuser",
            password_hash="hashed_password",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_brute_force_detection(self, anomaly_service, sample_user, db_session):
        """Test detection of multiple failed login attempts"""
        # Create multiple failed login attempts
        for i in range(6):  # Exceeds threshold of 5
            attempt = LoginAttempt(
                user_id=sample_user.id,
                username=sample_user.username,
                ip_address="192.168.1.100",
                is_successful=False,
                failure_reason="Invalid password",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i*2)  # Within 15 min window
            )
            db_session.add(attempt)
        await db_session.commit()

        # Calculate risk score
        risk_score = await anomaly_service.calculate_risk_score(
            user_id=sample_user.id,
            identifier=sample_user.username,
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )

        # Should detect brute force and assign high risk
        assert risk_score.total_score >= 3.0  # 6 attempts * weight 3.0
        assert "Multiple Failed Login Attempts" in risk_score.triggered_rules
        assert risk_score.risk_level.value in ['medium', 'high', 'critical']

    @pytest.mark.asyncio
    async def test_impossible_travel_detection(self, anomaly_service, sample_user, db_session):
        """Test detection of impossible travel scenarios"""
        # Create successful logins from distant locations within short time
        locations = [
            ("New York", 40.7128, -74.0060),  # New York
            ("London", 51.5074, -0.1278),     # London (impossible travel)
        ]

        base_time = datetime.now(timezone.utc)
        for i, (city, lat, lon) in enumerate(locations):
            attempt = LoginAttempt(
                user_id=sample_user.id,
                username=sample_user.username,
                ip_address=f"192.168.{i}.100",
                is_successful=True,
                timestamp=base_time - timedelta(minutes=i*30)  # 30 min apart
            )
            db_session.add(attempt)
        await db_session.commit()

        # Mock geolocation to return the test coordinates
        with patch.object(anomaly_service, '_get_geolocation_from_ip') as mock_geo:
            mock_geo.side_effect = [
                GeoLocation(lat, lon, city, city, "UTC") for city, lat, lon in locations
            ]

            risk_score = await anomaly_service.calculate_risk_score(
                user_id=sample_user.id,
                identifier=sample_user.username,
                ip_address="192.168.1.100",
                user_agent="Test Browser"
            )

            # Should detect impossible travel
            assert "Impossible Travel Scenario" in risk_score.triggered_rules
            assert risk_score.risk_level.value in ['high', 'critical']

    @pytest.mark.asyncio
    async def test_device_fingerprint_drift(self, anomaly_service, sample_user, db_session):
        """Test detection of device fingerprint changes"""
        # Create sessions with different fingerprints
        fingerprints = ["fp1_hash", "fp2_hash", "fp3_hash"]

        for i, fp in enumerate(fingerprints):
            session = UserSession(
                user_id=sample_user.id,
                username=sample_user.username,
                session_id=f"session_{i}",
                ip_address="192.168.1.100",
                created_at=datetime.now(timezone.utc) - timedelta(hours=i+1),
                device_fingerprint_hash=fp
            )
            db_session.add(session)
        await db_session.commit()

        # Check with a new fingerprint
        risk_score = await anomaly_service.calculate_risk_score(
            user_id=sample_user.id,
            identifier=sample_user.username,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            device_fingerprint="new_fp_hash"
        )

        # Should detect fingerprint drift
        assert "Device Fingerprint Drift" in risk_score.triggered_rules

    @pytest.mark.asyncio
    async def test_suspicious_ip_detection(self, anomaly_service):
        """Test detection of suspicious IP addresses"""
        suspicious_ips = ["0.0.0.0", "127.0.0.1", "10.0.0.1", "192.168.1.1"]

        for ip in suspicious_ips:
            risk_score = await anomaly_service.calculate_risk_score(
                user_id=None,
                identifier="testuser",
                ip_address=ip,
                user_agent="Test Browser"
            )

            # Should detect suspicious IP
            assert "Suspicious IP Address" in risk_score.triggered_rules

    @pytest.mark.asyncio
    async def test_rapid_session_creation(self, anomaly_service, sample_user, db_session):
        """Test detection of rapid session creation"""
        # Create multiple sessions within short time window
        for i in range(4):  # Exceeds threshold of 3
            session = UserSession(
                user_id=sample_user.id,
                username=sample_user.username,
                session_id=f"rapid_session_{i}",
                ip_address="192.168.1.100",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=i*2)  # Within 10 min
            )
            db_session.add(session)
        await db_session.commit()

        risk_score = await anomaly_service.calculate_risk_score(
            user_id=sample_user.id,
            identifier=sample_user.username,
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )

        # Should detect rapid session creation
        assert "Rapid Session Creation" in risk_score.triggered_rules

    @pytest.mark.asyncio
    async def test_risk_level_calculation(self, anomaly_service):
        """Test risk level calculation based on total score"""
        test_cases = [
            (0.5, RiskLevel.LOW),
            (2.5, RiskLevel.MEDIUM),
            (6.0, RiskLevel.HIGH),
            (12.0, RiskLevel.CRITICAL)
        ]

        for score, expected_level in test_cases:
            risk_score = RiskScore(total_score=score)
            anomaly_service._calculate_risk_level(risk_score)
            assert risk_score.risk_level == expected_level

    @pytest.mark.asyncio
    async def test_enforcement_action_selection(self, anomaly_service):
        """Test enforcement action selection based on risk level"""
        test_cases = [
            (RiskLevel.LOW, ["normal_rule"], EnforcementAction.LOG_ONLY),
            (RiskLevel.MEDIUM, ["failed_attempts"], EnforcementAction.RATE_LIMIT),
            (RiskLevel.HIGH, ["impossible_travel"], EnforcementAction.MFA_CHALLENGE),
            (RiskLevel.CRITICAL, ["brute_force"], EnforcementAction.ACCOUNT_LOCK)
        ]

        for risk_level, rules, expected_action in test_cases:
            risk_score = RiskScore(
                risk_level=risk_level,
                triggered_rules=rules
            )
            action = anomaly_service._get_recommended_action(risk_level, rules)
            assert action == expected_action

    @pytest.mark.asyncio
    async def test_anomaly_event_logging(self, anomaly_service, sample_user, db_session):
        """Test logging of anomaly events"""
        risk_score = RiskScore(
            total_score=8.0,
            risk_level=RiskLevel.HIGH,
            triggered_rules=["Multiple Failed Login Attempts"]
        )

        await anomaly_service.log_anomaly_event(
            user_id=sample_user.id,
            anomaly_type=AnomalyType.BRUTE_FORCE,
            risk_score=risk_score,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            details={"test": True}
        )

        # Verify event was logged
        stmt = select(AuthAnomalyEvent).where(AuthAnomalyEvent.user_id == sample_user.id)
        result = await db_session.execute(stmt)
        event = result.scalar_one_or_none()

        assert event is not None
        assert event.anomaly_type == AnomalyType.BRUTE_FORCE.value
        assert event.risk_level == RiskLevel.HIGH.value
        assert event.risk_score == 8.0
        assert event.ip_address == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_normal_behavior_no_false_positives(self, anomaly_service, sample_user, db_session):
        """Test that normal login behavior doesn't trigger false positives"""
        # Create normal successful login
        attempt = LoginAttempt(
            user_id=sample_user.id,
            username=sample_user.username,
            ip_address="192.168.1.100",
            is_successful=True,
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(attempt)
        await db_session.commit()

        risk_score = await anomaly_service.calculate_risk_score(
            user_id=sample_user.id,
            identifier=sample_user.username,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Should not trigger any rules for normal behavior
        assert len(risk_score.triggered_rules) == 0
        assert risk_score.risk_level == RiskLevel.LOW
        assert risk_score.recommended_action == EnforcementAction.NONE

    @pytest.mark.asyncio
    async def test_geo_distance_calculation(self):
        """Test geographic distance calculations"""
        # Test locations
        nyc = GeoLocation(40.7128, -74.0060, "New York", "New York", "EST")
        london = GeoLocation(51.5074, -0.1278, "London", "London", "GMT")

        distance = nyc.distance_to(london)
        # Distance between NYC and London is approximately 5570 km
        assert 5500 <= distance <= 5700

        # Test same location
        same_location = GeoLocation(40.7128, -74.0060, "New York", "New York", "EST")
        assert nyc.distance_to(same_location) < 1  # Very close


class TestAuthAnomalyMiddleware:
    """Test suite for AuthAnomalyMiddleware"""

    @pytest.fixture
    def middleware(self):
        """Create AuthAnomalyMiddleware instance"""
        from ..middleware.auth_anomaly_middleware import AuthAnomalyMiddleware
        return AuthAnomalyMiddleware(lambda: None)

    def test_auth_endpoint_detection(self, middleware):
        """Test detection of authentication endpoints"""
        auth_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v1/auth/verify-2fa"
        ]

        for endpoint in auth_endpoints:
            assert middleware._is_auth_endpoint(endpoint)

        non_auth_endpoints = [
            "/api/v1/users/profile",
            "/api/v1/health",
            "/api/v1/questions"
        ]

        for endpoint in non_auth_endpoints:
            assert not middleware._is_auth_endpoint(endpoint)

    @pytest.mark.asyncio
    async def test_enforcement_action_application(self, middleware):
        """Test application of enforcement actions"""
        from ..middleware.auth_anomaly_middleware import AuthAnomalyMiddleware

        # Test rate limiting action
        request = MagicMock()
        request.state = {}

        await middleware._apply_enforcement_action(EnforcementAction.RATE_LIMIT, request)
        assert request.state.get("anomaly_enforcement") == "rate_limited"

        # Test MFA challenge action
        await middleware._apply_enforcement_action(EnforcementAction.MFA_CHALLENGE, request)
        assert request.state.get("anomaly_enforcement") == "mfa_required"

        # Test account lock action (should raise exception)
        with pytest.raises(Exception):  # HTTPException
            await middleware._apply_enforcement_action(EnforcementAction.ACCOUNT_LOCK, request)


class TestAnomalyDetectionIntegration:
    """Integration tests for anomaly detection in auth flow"""

    @pytest.mark.asyncio
    async def test_brute_force_prevention_integration(self, client, db_session):
        """Test that brute force attempts are blocked by middleware"""
        # This would require setting up a full FastAPI test client
        # with the middleware enabled
        pass

    @pytest.mark.asyncio
    async def test_anomaly_stats_reporting(self, anomaly_service, sample_user, db_session):
        """Test anomaly statistics reporting"""
        # Create some anomaly events
        events_data = [
            (AnomalyType.BRUTE_FORCE, RiskLevel.HIGH, 7.5),
            (AnomalyType.BRUTE_FORCE, RiskLevel.MEDIUM, 3.2),
            (AnomalyType.IMPOSSIBLE_TRAVEL, RiskLevel.CRITICAL, 15.0)
        ]

        for anomaly_type, risk_level, score in events_data:
            risk_score = RiskScore(total_score=score, risk_level=risk_level)
            await anomaly_service.log_anomaly_event(
                user_id=sample_user.id,
                anomaly_type=anomaly_type,
                risk_score=risk_score,
                ip_address="192.168.1.100",
                user_agent="Test Browser"
            )

        # Get stats
        stats = await anomaly_service.get_anomaly_stats(user_id=sample_user.id, hours=24)

        assert AnomalyType.BRUTE_FORCE.value in stats
        assert AnomalyType.IMPOSSIBLE_TRAVEL.value in stats
        assert stats[AnomalyType.BRUTE_FORCE.value]["count"] == 2
        assert stats[AnomalyType.IMPOSSIBLE_TRAVEL.value]["count"] == 1

    @pytest.mark.asyncio
    async def test_performance_under_load(self, anomaly_service, sample_user, db_session):
        """Test that anomaly detection performs well under load"""
        import time

        # Create many login attempts
        attempts = []
        for i in range(100):
            attempt = LoginAttempt(
                user_id=sample_user.id,
                username=sample_user.username,
                ip_address=f"192.168.{i%10}.100",
                is_successful=i % 10 != 0,  # 10% success rate
                failure_reason="Invalid password" if i % 10 != 0 else None,
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i)
            )
            attempts.append(attempt)

        db_session.add_all(attempts)
        await db_session.commit()

        # Measure performance
        start_time = time.time()
        risk_score = await anomaly_service.calculate_risk_score(
            user_id=sample_user.id,
            identifier=sample_user.username,
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        end_time = time.time()

        # Should complete in reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        # Should detect brute force from the failed attempts
        assert risk_score.total_score > 0