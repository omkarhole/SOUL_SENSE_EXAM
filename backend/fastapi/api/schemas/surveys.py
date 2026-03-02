from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from ..models import SurveyStatus, QuestionType

class SurveyQuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    options: Optional[List[Dict[str, Any]]] = None # [{"label": "Rarely", "value": 0}, ...]
    is_required: bool = True
    order: int = 0
    logic_config: Optional[Dict[str, Any]] = None

class SurveyQuestionCreate(SurveyQuestionBase):
    pass

class SurveyQuestionResponse(SurveyQuestionBase):
    id: int

class SurveySectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0

class SurveySectionCreate(SurveySectionBase):
    questions: List[SurveyQuestionCreate] = []

class SurveySectionResponse(SurveySectionBase):
    id: int
    questions: List[SurveyQuestionResponse] = []

class SurveyTemplateBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: SurveyStatus = SurveyStatus.DRAFT
    is_active: bool = False
    scoring_logic: Optional[List[Dict[str, Any]]] = None # The DSL

class SurveyTemplateCreate(SurveyTemplateBase):
    sections: List[SurveySectionCreate] = []

class SurveyTemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SurveyStatus] = None
    is_active: Optional[bool] = None
    scoring_logic: Optional[List[Dict[str, Any]]] = None
    
class SurveyTemplateResponse(SurveyTemplateBase):
    id: int
    uuid: str
    version: int
    created_at: datetime
    updated_at: datetime
    sections: List[SurveySectionResponse] = []

# Submissions
class SurveyResponseCreate(BaseModel):
    question_id: int
    answer_value: str

class SurveySubmissionCreate(BaseModel):
    survey_id: int
    responses: List[SurveyResponseCreate]
    metadata_json: Optional[Dict[str, Any]] = None

class SurveySubmissionResponse(BaseModel):
    id: int
    survey_id: int
    total_scores: Optional[Dict[str, float]] = None
    completed_at: Optional[datetime] = None
