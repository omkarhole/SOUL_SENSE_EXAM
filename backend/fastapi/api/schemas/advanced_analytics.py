from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CorrelationResult(BaseModel):
    variable_a: str
    variable_b: str
    correlation_coefficient: float
    significance: str
    description: str

class DemographicBenchmark(BaseModel):
    category: str
    user_value: float
    population_average: float
    percentile: float
    comparison_text: str

class AnomalyEvent(BaseModel):
    type: str = "emotional_decline"
    severity: str
    date: datetime
    previous_average: float
    current_value: float
    drop_percentage: float

class AdvancedInsightsResponse(BaseModel):
    correlations: List[CorrelationResult]
    benchmarks: List[DemographicBenchmark]
    anomalies: List[AnomalyEvent]
    actionable_advice: List[str]
    generated_at: datetime
