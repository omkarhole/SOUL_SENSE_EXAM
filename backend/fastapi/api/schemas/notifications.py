from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NotificationPreferenceBase(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    marketing_alerts: Optional[bool] = None
    security_alerts: Optional[bool] = None
    insight_alerts: Optional[bool] = None
    reminder_alerts: Optional[bool] = None

class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: int
    user_id: int

class NotificationTemplateCreate(BaseModel):
    name: str
    subject_template: str
    body_html_template: Optional[str] = None
    body_text_template: Optional[str] = None
    language: str = "en"
    is_active: bool = True

class NotificationTemplateResponse(NotificationTemplateCreate):
    id: int

class NotificationSendRequest(BaseModel):
    user_id: int
    template_name: str
    context: Dict[str, Any] = {}
    force_channels: Optional[List[str]] = None

class NotificationLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    template_name: str
    channel: str
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
