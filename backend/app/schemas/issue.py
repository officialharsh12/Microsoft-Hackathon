from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class TimelinePoint(BaseModel):
    date: str
    count: int

class IssueItem(BaseModel):
    id: int
    dataset_id: int
    cluster_id: int
    theme: str
    review_count: int
    negative_percentage: float
    dominant_emotion: str
    severity: str
    severity_score: float
    severity_reason: str
    trend: str
    trend_direction: str
    trend_percentage: Optional[float] = None
    is_emerging: bool
    sample_quotes: Optional[List[str]] = None
    timeline: Optional[List[TimelinePoint]] = None

class DetectionRationale(BaseModel):
    summary: str
    review_volume: str
    sentiment_signal: str
    emotional_resonance: str
    severity_level: str
    trend_trajectory: str

class EvidenceReview(BaseModel):
    id: Optional[int] = None
    original_id: Optional[str] = None
    text: str
    cleaned_text: str
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    emotion: Optional[str] = None
    emotion_score: Optional[float] = None
    rating: Optional[float] = None
    date: Optional[str] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None

class IssueEvidenceResponse(BaseModel):
    issue_id: int
    theme: str
    severity: str
    severity_score: float
    negative_percentage: float
    dominant_emotion: str
    trend: str
    detection_rationale: Dict[str, str]
    evidence_count: int
    total_related_reviews: int
    evidence_reviews: List[EvidenceReview]

class DashboardStats(BaseModel):
    dataset_id: Optional[int] = None
    dataset_filename: Optional[str] = None
    total_reviews: int
    positive_percentage: float
    negative_percentage: float
    high_severity_count: int
    emerging_issues_count: int
    sentiment_distribution: List[Dict[str, Any]]
    emotion_distribution: List[Dict[str, Any]]
    severity_distribution: List[Dict[str, Any]]
    top_issues: List[IssueItem]
    emerging_issues: List[IssueItem]
    trend_timeline: List[Dict[str, Any]]
