from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class ActivityItem(BaseModel):
    id: str
    action: str
    target_type: str
    description: str
    timestamp: datetime

class DashboardSummaryResponse(BaseModel):
    total_documents: int
    completed_documents: int
    failed_documents: int
    questions_asked: int
    detected_conflicts: int
    unresolved_conflicts: int
    recent_activity: List[ActivityItem] = []

class MetricScore(BaseModel):
    metric_name: str
    score: float
    description: str
    sample_size: int

class EvaluationSummaryResponse(BaseModel):
    evaluation_title: str
    total_eval_queries: int
    metrics: List[MetricScore]
    evaluated_at: datetime
    synthetic_demo_included: bool
    notes: str
