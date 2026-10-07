from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class CSVUploadResponse(BaseModel):
    dataset_id: int
    filename: str
    total_rows: int
    columns: List[str]
    detected_text_column: Optional[str] = None
    detected_date_column: Optional[str] = None
    detected_rating_column: Optional[str] = None
    detected_id_column: Optional[str] = None
    sample_rows: List[Dict[str, Any]]

class AnalysisRequest(BaseModel):
    dataset_id: int
    text_column: str
    date_column: Optional[str] = None
    rating_column: Optional[str] = None
    id_column: Optional[str] = None
    platform_column: Optional[str] = None
    version_column: Optional[str] = None

class AnalysisResponse(BaseModel):
    dataset_id: int
    status: str
    message: str
    total_reviews_analyzed: int
    issues_discovered: int
    emerging_issues_count: int

class ReviewItem(BaseModel):
    id: int
    dataset_id: int
    original_id: Optional[str]
    raw_text: str
    cleaned_text: str
    review_date: Optional[str] = None
    rating: Optional[float] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    emotion: Optional[str] = None
    emotion_score: Optional[float] = None
    cluster_id: Optional[int] = None
