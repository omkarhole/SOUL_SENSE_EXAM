from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import List, Optional, Dict, Any
from ..services.feature_flags import get_feature_service
from ..routers.auth import require_admin
from ..models import User

router = APIRouter(prefix="/flags", tags=["Feature Flags"])

@router.get("/")
async def list_flags(current_user: User = Depends(require_admin)):
    """List all feature flags available in Consul."""
    service = get_feature_service()
    return service.get_all_flags()

@router.post("/")
async def create_or_update_flag(
    feature_name: str = Query(...),
    config: Dict[str, Any] = Body(...), # {enabled: bool, rollout_percentage: int, tenant_overrides: {...}}
    current_user: User = Depends(require_admin)
):
    """Admin only: Toggle, rollout or override a specific feature flag."""
    service = get_feature_service()
    
    # Validation of the config object
    if not isinstance(config.get('enabled'), bool):
         raise HTTPException(status_code=400, detail="'enabled' must be boolean")
    
    success = service.set_flag(feature_name, config)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to write to Consul")
    
    return {"message": f"Flag '{feature_name}' updated successfully.", "config": config}

@router.delete("/")
async def delete_flag(
    feature_name: str = Query(...),
    current_user: User = Depends(require_admin)
):
    """Admin only: Remove a feature flag entirely."""
    service = get_feature_service()
    try:
        service.client.kv.delete(f"soulsense/features/{feature_name}")
        service.cache.clear()
        return {"message": f"Flag '{feature_name}' deleted."}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
