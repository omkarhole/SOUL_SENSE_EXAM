"""
Auth Anomaly Detection Service #1263
=====================================

Implements baseline anomaly detection rules for authentication security.
Provides real-time risk scoring and enforcement actions for suspicious login behavior.

Features:
- Multiple failed login attempts detection
- Impossible travel scenario detection
- Token refresh abuse detection
- User-agent/device fingerprint drift detection
- Risk scoring model per session and per user
- Enforcement tiers (MFA challenge, rate limit, temporary lock)
- Comprehensive anomaly event logging
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.sql import text

from ..models import LoginAttempt, UserSession, User, AuthAnomalyEvent
from ..config import get_settings_instance
from .audit_service import AuditService

logger = logging.getLogger(__name__)
settings = get_settings_instance()


class AnomalyType(Enum):
    """Types of authentication anomalies"""
    BRUTE_FORCE = "brute_force"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    TOKEN_REFRESH_ABUSE = "token_refresh_abuse"
    DEVICE_FINGERPRINT_DRIFT = "device_fingerprint_drift"
    SUSPICIOUS_IP = "suspicious_ip"
    RAPID_SESSION_CREATION = "rapid_session_creation"


class RiskLevel(Enum):
    """Risk levels for anomaly scoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnforcementAction(Enum):
    """Enforcement actions for anomalies"""
    NONE = "none"
    LOG_ONLY = "log_only"
    MFA_CHALLENGE = "mfa_challenge"
    RATE_LIMIT = "rate_limit"
    TEMPORARY_LOCK = "temporary_lock"
    ACCOUNT_LOCK = "account_lock"


@dataclass
class AnomalyRule:
    """Configuration for an anomaly detection rule"""
    name: str
    anomaly_type: AnomalyType
    enabled: bool = True
    threshold: float = 0.0
    time_window_minutes: int = 60
    risk_weight: float = 1.0
    enforcement_action: EnforcementAction = EnforcementAction.LOG_ONLY
    description: str = ""


@dataclass
class RiskScore:
    """Risk scoring result"""
    total_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    triggered_rules: List[str] = field(default_factory=list)
    recommended_action: EnforcementAction = EnforcementAction.NONE
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeoLocation:
    """Geographic location data"""
    latitude: float
    longitude: float
    country: str = ""
    city: str = ""
    timezone: str = ""

    @property
    def coordinates(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    def distance_to(self, other: 'GeoLocation') -> float:
        """Calculate distance between two locations in kilometers"""
        # Haversine formula
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return 6371 * c  # Earth radius in kilometers


class AuthAnomalyService:
    """
    Service for detecting authentication anomalies and managing risk scoring.
    Implements baseline rules for identifying suspicious login behavior.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[AnomalyType, AnomalyRule]:
        """Initialize baseline anomaly detection rules"""
        return {
            AnomalyType.BRUTE_FORCE: AnomalyRule(
                name="Multiple Failed Login Attempts",
                anomaly_type=AnomalyType.BRUTE_FORCE,
                threshold=5.0,  # 5+ failed attempts
                time_window_minutes=15,
                risk_weight=3.0,
                enforcement_action=EnforcementAction.RATE_LIMIT,
                description="Detects multiple failed login attempts within a short time window"
            ),
            AnomalyType.IMPOSSIBLE_TRAVEL: AnomalyRule(
                name="Impossible Travel Scenario",
                anomaly_type=AnomalyType.IMPOSSIBLE_TRAVEL,
                threshold=500.0,  # 500+ km in unrealistic time
                time_window_minutes=60,
                risk_weight=4.0,
                enforcement_action=EnforcementAction.MFA_CHALLENGE,
                description="Detects logins from geographically distant locations within unrealistic time"
            ),
            AnomalyType.TOKEN_REFRESH_ABUSE: AnomalyRule(
                name="Token Refresh Abuse",
                anomaly_type=AnomalyType.TOKEN_REFRESH_ABUSE,
                threshold=10.0,  # 10+ refresh attempts
                time_window_minutes=30,
                risk_weight=2.5,
                enforcement_action=EnforcementAction.RATE_LIMIT,
                description="Detects sudden spikes in token refresh attempts"
            ),
            AnomalyType.DEVICE_FINGERPRINT_DRIFT: AnomalyRule(
                name="Device Fingerprint Drift",
                anomaly_type=AnomalyType.DEVICE_FINGERPRINT_DRIFT,
                threshold=1.0,  # Any drift detected
                time_window_minutes=1440,  # 24 hours
                risk_weight=2.0,
                enforcement_action=EnforcementAction.MFA_CHALLENGE,
                description="Detects user-agent or device fingerprint changes during active session"
            ),
            AnomalyType.SUSPICIOUS_IP: AnomalyRule(
                name="Suspicious IP Address",
                anomaly_type=AnomalyType.SUSPICIOUS_IP,
                threshold=1.0,  # Any match with suspicious patterns
                time_window_minutes=60,
                risk_weight=1.5,
                enforcement_action=EnforcementAction.LOG_ONLY,
                description="Detects logins from known suspicious IP ranges"
            ),
            AnomalyType.RAPID_SESSION_CREATION: AnomalyRule(
                name="Rapid Session Creation",
                anomaly_type=AnomalyType.RAPID_SESSION_CREATION,
                threshold=3.0,  # 3+ sessions
                time_window_minutes=10,
                risk_weight=2.0,
                enforcement_action=EnforcementAction.RATE_LIMIT,
                description="Detects rapid creation of multiple sessions"
            )
        }

    async def _get_geolocation_from_ip(self, ip_address: str) -> Optional[GeoLocation]:
        """
        Get geographic location from IP address.
        In production, this would use a GeoIP service like MaxMind.
        For now, returns mock data based on IP patterns.
        """
        # Mock geolocation service - in production, integrate with MaxMind or similar
        if not ip_address or ip_address == "127.0.0.1" or ip_address.startswith("192.168."):
            return GeoLocation(0.0, 0.0, "Local", "Local", "UTC")

        # Simple mock based on IP patterns
        ip_hash = int(hashlib.md5(ip_address.encode()).hexdigest()[:8], 16)
        lat = (ip_hash % 180) - 90
        lon = (ip_hash % 360) - 180

        return GeoLocation(lat, lon, "Unknown", "Unknown", "UTC")

    async def _check_brute_force_attempts(self, identifier: str, ip_address: str) -> float:
        """Check for multiple failed login attempts"""
        time_window = datetime.now(timezone.utc) - timedelta(minutes=self._rules[AnomalyType.BRUTE_FORCE].time_window_minutes)

        stmt = select(func.count(LoginAttempt.id)).where(
            and_(
                or_(LoginAttempt.username == identifier, LoginAttempt.ip_address == ip_address),
                LoginAttempt.timestamp >= time_window,
                LoginAttempt.is_successful == False
            )
        )

        result = await self.db.execute(stmt)
        failed_count = result.scalar() or 0

        return float(failed_count)

    async def _check_impossible_travel(self, user_id: int, current_ip: str) -> float:
        """Check for impossible travel scenarios"""
        # Get recent successful logins
        time_window = datetime.now(timezone.utc) - timedelta(minutes=self._rules[AnomalyType.IMPOSSIBLE_TRAVEL].time_window_minutes)

        stmt = select(LoginAttempt).where(
            and_(
                LoginAttempt.user_id == user_id,
                LoginAttempt.timestamp >= time_window,
                LoginAttempt.is_successful == True
            )
        ).order_by(desc(LoginAttempt.timestamp)).limit(5)

        result = await self.db.execute(stmt)
        recent_logins = result.scalars().all()

        if len(recent_logins) < 2:
            return 0.0

        current_location = await self._get_geolocation_from_ip(current_ip)
        if not current_location:
            return 0.0

        max_distance = 0.0
        for login in recent_logins:
            if login.ip_address == current_ip:
                continue

            prev_location = await self._get_geolocation_from_ip(login.ip_address)
            if prev_location:
                distance = current_location.distance_to(prev_location)
                max_distance = max(max_distance, distance)

        return max_distance

    async def _check_token_refresh_abuse(self, user_id: int) -> float:
        """Check for token refresh abuse"""
        # This would need to be integrated with token refresh logging
        # For now, return 0 as we don't have refresh attempt tracking yet
        return 0.0

    async def _check_device_fingerprint_drift(self, user_id: int, current_fingerprint: str) -> float:
        """Check for device fingerprint drift"""
        if not current_fingerprint:
            return 0.0

        # Get recent sessions for this user
        time_window = datetime.now(timezone.utc) - timedelta(minutes=self._rules[AnomalyType.DEVICE_FINGERPRINT_DRIFT].time_window_minutes)

        stmt = select(UserSession.device_fingerprint_hash).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.created_at >= time_window,
                UserSession.device_fingerprint_hash.isnot(None)
            )
        ).distinct()

        result = await self.db.execute(stmt)
        recent_fingerprints = [row[0] for row in result.all()]

        # Check if current fingerprint differs from recent ones
        if current_fingerprint not in recent_fingerprints and recent_fingerprints:
            return 1.0  # Drift detected

        return 0.0

    async def _check_suspicious_ip(self, ip_address: str) -> float:
        """Check if IP address matches suspicious patterns"""
        # Simple checks for known suspicious patterns
        suspicious_patterns = [
            "0.0.0.0",
            "127.0.0.1",
            "10.0.0.0/8",  # Private networks (simplified)
            "172.16.0.0/12",
            "192.168.0.0/16"
        ]

        for pattern in suspicious_patterns:
            if pattern in ip_address:
                return 1.0

        return 0.0

    async def _check_rapid_session_creation(self, user_id: int) -> float:
        """Check for rapid session creation"""
        time_window = datetime.now(timezone.utc) - timedelta(minutes=self._rules[AnomalyType.RAPID_SESSION_CREATION].time_window_minutes)

        stmt = select(func.count(UserSession.id)).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.created_at >= time_window
            )
        )

        result = await self.db.execute(stmt)
        session_count = result.scalar() or 0

        return float(session_count)

    async def calculate_risk_score(
        self,
        user_id: Optional[int],
        identifier: str,
        ip_address: str,
        user_agent: str = "",
        device_fingerprint: str = ""
    ) -> RiskScore:
        """
        Calculate risk score for authentication attempt based on anomaly rules.
        """
        risk_score = RiskScore()
        triggered_rules = []

        # Check each enabled rule
        for rule in self._rules.values():
            if not rule.enabled:
                continue

            rule_score = 0.0

            try:
                if rule.anomaly_type == AnomalyType.BRUTE_FORCE:
                    rule_score = await self._check_brute_force_attempts(identifier, ip_address)

                elif rule.anomaly_type == AnomalyType.IMPOSSIBLE_TRAVEL and user_id:
                    rule_score = await self._check_impossible_travel(user_id, ip_address)

                elif rule.anomaly_type == AnomalyType.TOKEN_REFRESH_ABUSE and user_id:
                    rule_score = await self._check_token_refresh_abuse(user_id)

                elif rule.anomaly_type == AnomalyType.DEVICE_FINGERPRINT_DRIFT and user_id:
                    rule_score = await self._check_device_fingerprint_drift(user_id, device_fingerprint)

                elif rule.anomaly_type == AnomalyType.SUSPICIOUS_IP:
                    rule_score = await self._check_suspicious_ip(ip_address)

                elif rule.anomaly_type == AnomalyType.RAPID_SESSION_CREATION and user_id:
                    rule_score = await self._check_rapid_session_creation(user_id)

                # Check if rule threshold is exceeded
                if rule_score >= rule.threshold:
                    weighted_score = rule_score * rule.risk_weight
                    risk_score.total_score += weighted_score
                    triggered_rules.append(rule.name)
                    risk_score.details[rule.name] = {
                        "score": rule_score,
                        "threshold": rule.threshold,
                        "weighted_score": weighted_score
                    }

            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {e}")
                continue

        # Determine risk level
        if risk_score.total_score >= 10.0:
            risk_score.risk_level = RiskLevel.CRITICAL
        elif risk_score.total_score >= 5.0:
            risk_score.risk_level = RiskLevel.HIGH
        elif risk_score.total_score >= 2.0:
            risk_score.risk_level = RiskLevel.MEDIUM
        else:
            risk_score.risk_level = RiskLevel.LOW

        # Determine recommended enforcement action
        risk_score.triggered_rules = triggered_rules
        risk_score.recommended_action = self._get_recommended_action(risk_score.risk_level, triggered_rules)

        return risk_score

    def _get_recommended_action(self, risk_level: RiskLevel, triggered_rules: List[str]) -> EnforcementAction:
        """Determine recommended enforcement action based on risk level and triggered rules"""
        if risk_level == RiskLevel.CRITICAL:
            return EnforcementAction.ACCOUNT_LOCK
        elif risk_level == RiskLevel.HIGH:
            # Check for specific high-risk rules
            if any("Impossible Travel" in rule for rule in triggered_rules):
                return EnforcementAction.MFA_CHALLENGE
            return EnforcementAction.TEMPORARY_LOCK
        elif risk_level == RiskLevel.MEDIUM:
            return EnforcementAction.RATE_LIMIT
        else:
            return EnforcementAction.LOG_ONLY

    async def log_anomaly_event(
        self,
        user_id: Optional[int],
        anomaly_type: AnomalyType,
        risk_score: RiskScore,
        ip_address: str,
        user_agent: str = "",
        details: Dict[str, Any] = None
    ) -> None:
        """Log anomaly event to database and audit system"""
        try:
            # Create anomaly event record
            anomaly_event = AuthAnomalyEvent(
                user_id=user_id,
                anomaly_type=anomaly_type.value,
                risk_level=risk_score.risk_level.value,
                risk_score=risk_score.total_score,
                ip_address=ip_address,
                user_agent=user_agent,
                triggered_rules=json.dumps(risk_score.triggered_rules),
                details=json.dumps(details or risk_score.details)
            )

            self.db.add(anomaly_event)
            await self.db.commit()

            # Log to audit system
            await AuditService.log_security_event(
                user_id=user_id,
                event_type="AUTH_ANOMALY_DETECTED",
                details={
                    "anomaly_type": anomaly_type.value,
                    "risk_level": risk_score.risk_level.value,
                    "risk_score": risk_score.total_score,
                    "triggered_rules": risk_score.triggered_rules,
                    "ip_address": ip_address,
                    "recommended_action": risk_score.recommended_action.value
                }
            )

            logger.warning(
                f"Auth anomaly detected: {anomaly_type.value} for user {user_id} "
                f"(risk: {risk_score.risk_level.value}, score: {risk_score.total_score:.2f})"
            )

        except Exception as e:
            logger.error(f"Failed to log anomaly event: {e}")

    async def should_enforce_action(
        self,
        risk_score: RiskScore,
        current_user_state: Dict[str, Any] = None
    ) -> Tuple[bool, EnforcementAction]:
        """
        Determine if enforcement action should be taken based on risk score and user state.
        """
        action = risk_score.recommended_action

        # Apply business logic overrides
        if current_user_state:
            # Don't lock admin accounts unless critical
            if current_user_state.get("is_admin") and risk_score.risk_level != RiskLevel.CRITICAL:
                action = EnforcementAction.MFA_CHALLENGE

            # Recently verified users get more leniency
            if current_user_state.get("recently_verified", False):
                if action == EnforcementAction.TEMPORARY_LOCK:
                    action = EnforcementAction.RATE_LIMIT

        # Only enforce if action is not NONE or LOG_ONLY
        should_enforce = action not in [EnforcementAction.NONE, EnforcementAction.LOG_ONLY]

        return should_enforce, action

    def _calculate_risk_level(self, risk_score: RiskScore) -> None:
        """Calculate and set the risk level based on total score"""
        if risk_score.total_score >= 10.0:
            risk_score.risk_level = RiskLevel.CRITICAL
        elif risk_score.total_score >= 5.0:
            risk_score.risk_level = RiskLevel.HIGH
        elif risk_score.total_score >= 2.0:
            risk_score.risk_level = RiskLevel.MEDIUM
        else:
            risk_score.risk_level = RiskLevel.LOW

    async def get_anomaly_stats(self, user_id: Optional[int] = None, hours: int = 24) -> Dict[str, Any]:
        """Get anomaly statistics for reporting"""
        time_window = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(
            AuthAnomalyEvent.anomaly_type,
            func.count(AuthAnomalyEvent.id).label('count'),
            func.avg(AuthAnomalyEvent.risk_score).label('avg_risk')
        ).where(AuthAnomalyEvent.created_at >= time_window)

        if user_id:
            query = query.where(AuthAnomalyEvent.user_id == user_id)

        query = query.group_by(AuthAnomalyEvent.anomaly_type)

        result = await self.db.execute(query)
        stats = {}
        for row in result.all():
            stats[row.anomaly_type] = {
                "count": row.count,
                "avg_risk_score": float(row.avg_risk) if row.avg_risk else 0.0
            }

        return stats