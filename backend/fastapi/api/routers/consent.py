"""
Consent management API endpoints for privacy compliance.

Provides endpoints for tracking consent events and managing user consent preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from ..schemas import (
    ConsentEventCreate,
    ConsentStatusResponse,
    ConsentUpdateRequest
)
from ..services.analytics_service import AnalyticsService
from ..services.db_service import get_db
from ..middleware.rate_limiter import rate_limit_analytics

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/track", response_model=Dict[str, Any], dependencies=[Depends(rate_limit_analytics)])
async def track_consent_event(
    event: ConsentEventCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track a consent event (consent_given or consent_revoked).

    This endpoint logs consent events for privacy compliance tracking.
    """
    try:
        # Track the consent event
        result = AnalyticsService.track_consent_event(
            db=db,
            anonymous_id=event.anonymous_id,
            event_type=event.event_type,
            consent_version=event.consent_version,
            ip_address=request.client.host if request.client else None
        )

        return {
            "success": True,
            "message": f"Consent event '{event.event_type}' tracked successfully",
            "event_id": result.get("event_id"),
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track consent event: {str(e)}")


@router.get("/status/{anonymous_id}", response_model=ConsentStatusResponse)
async def get_consent_status(
    anonymous_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current consent status for a user.

    Returns whether analytics consent has been given and other consent preferences.
    """
    try:
        consent_status = AnalyticsService.get_consent_status(db, anonymous_id)

        return ConsentStatusResponse(
            anonymous_id=anonymous_id,
            analytics_consent_given=consent_status.get('analytics_consent_given', False),
            consent_version=consent_status.get('consent_version'),
            last_updated=consent_status.get('last_updated'),
            consent_events_count=consent_status.get('consent_events_count', 0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consent status: {str(e)}")


@router.put("/preferences/{anonymous_id}", response_model=Dict[str, Any], dependencies=[Depends(rate_limit_analytics)])
async def update_consent_preferences(
    anonymous_id: str,
    preferences: ConsentUpdateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Update user consent preferences.

    This endpoint allows users to update their consent preferences and tracks the change.
    """
    try:
        # Update consent preferences
        result = AnalyticsService.update_consent_preferences(
            db=db,
            anonymous_id=anonymous_id,
            analytics_consent=preferences.analytics_consent_given,
            consent_version=preferences.consent_version,
            ip_address=request.client.host if request.client else None
        )

        return {
            "success": True,
            "message": "Consent preferences updated successfully",
            "anonymous_id": anonymous_id,
            "analytics_consent_given": preferences.analytics_consent_given,
            "consent_version": preferences.consent_version,
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update consent preferences: {str(e)}")


@router.get("/check/{anonymous_id}")
async def check_analytics_consent(
    anonymous_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if analytics consent is given for a user.

    This is a lightweight endpoint for quick consent checks.
    """
    try:
        consent_status = AnalyticsService.check_analytics_consent(db, anonymous_id)

        return {
            "anonymous_id": anonymous_id,
            "analytics_consent_given": consent_status.get('analytics_consent_given', False),
            "consent_version": consent_status.get('consent_version'),
            "last_updated": consent_status.get('last_updated')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check consent: {str(e)}")