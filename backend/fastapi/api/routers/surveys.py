from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

from ..services.db_service import get_db
from ..services.survey_service import SurveyService
from ..schemas.surveys import (
    SurveyTemplateCreate, SurveyTemplateResponse,
    SurveySubmissionCreate, SurveySubmissionResponse,
    SurveyTemplateUpdate
)
from .auth import get_current_user, require_admin
from ..models import User

router = APIRouter(tags=["Surveys"])

async def get_survey_service(db: AsyncSession = Depends(get_db)):
    return SurveyService(db)

# PUBLIC / USER ENDPOINTS
@router.get("/active", response_model=List[SurveyTemplateResponse])
async def list_active_surveys(
    service: Annotated[SurveyService, Depends(get_survey_service)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get all published and active survey templates.
    Users can browse active assessments to take them.
    """
    return await service.get_active_surveys()

@router.post("/submit", response_model=SurveySubmissionResponse)
async def submit_survey(
    submission: SurveySubmissionCreate,
    service: Annotated[SurveyService, Depends(get_survey_service)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Submit responses for a survey.
    The system will automatically apply the Scoring DSL rules to calculate 
    dimension-specific scores (e.g. Anxiety, Resilience).
    """
    try:
        return await service.submit_responses(
            user_id=current_user.id,
            survey_id=submission.survey_id,
            responses=[r.model_dump() for r in submission.responses],
            metadata=submission.metadata_json
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ADMIN ENDPOINTS
@router.post("/", response_model=SurveyTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_survey_template(
    template: SurveyTemplateCreate,
    service: Annotated[SurveyService, Depends(get_survey_service)],
    admin_user: Annotated[User, Depends(require_admin)]
):
    """
    Create a new survey draft (Admin only).
    Suppports nested sections and questions.
    """
    return await service.create_template(admin_user.id, template.model_dump())

@router.post("/{template_id}/publish", response_model=SurveyTemplateResponse)
async def publish_survey_template(
    template_id: int,
    service: Annotated[SurveyService, Depends(get_survey_service)],
    admin_user: Annotated[User, Depends(require_admin)]
):
    """
    Publish a survey template (Admin only).
    This will set the template as active and deactivate any older versions of the same survey.
    """
    try:
        return await service.publish_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{template_id}/version", response_model=SurveyTemplateResponse)
async def increment_survey_version(
    template_id: int,
    service: Annotated[SurveyService, Depends(get_survey_service)],
    admin_user: Annotated[User, Depends(require_admin)]
):
    """
    Clone an existing template to create a new version as a DRAFT (Admin only).
    Allows making changes without affecting historical data.
    """
    try:
        return await service.create_new_version(template_id, admin_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{template_id}", response_model=SurveyTemplateResponse)
async def get_survey_detail(
    template_id: int,
    service: Annotated[SurveyService, Depends(get_survey_service)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get full detailed structure of a survey including sections, questions, and logic."""
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
