from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..services.db_service import get_db
from ..services.correlation_service import CorrelationService
from ..schemas.advanced_analytics import AdvancedInsightsResponse
from .auth import get_current_user
from ..models import User

router = APIRouter(tags=["Advanced Analytics"])

@router.get("/insights", response_model=AdvancedInsightsResponse)
async def get_behavioral_insights(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Generate advanced behavioral insights using the Correlation Engine.
    
    This endpoint analyzes:
    - **Correlation**: Link between assessment scores and sentiment.
    - **Anomaly Detection**: Sudden emotional declines in recent days.
    - **Benchmarking**: Comparison against platform-wide population averages.
    - **Actionable AI**: Personalized advice generated from raw data correlations.
    """
    try:
        return await CorrelationService.get_advanced_insights(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger("api.analytics").error(f"Advanced insights failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to run the correlation engine")
