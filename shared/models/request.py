"""
Request and response data models.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Location(BaseModel):
    """Geographic location information."""
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    x_value: Optional[float] = None
    y_value: Optional[float] = None
    zipcode: Optional[str] = None
    council_district: Optional[str] = None
    neighborhood: Optional[str] = None
    police_precinct: Optional[str] = None


class ProcessedInput(BaseModel):
    """Processed user input from text or audio."""
    text: str
    confidence: float = 1.0
    language: str = "en"
    processing_time_ms: float = 0.0


class ExtractedEntities(BaseModel):
    """Entities extracted from user input."""
    location: Optional[Location] = None
    location_type: Optional[str] = None  # "address" | "intersection" | "landmark" | "area"
    service_keywords: List[str] = Field(default_factory=list)
    urgency_indicators: List[str] = Field(default_factory=list)
    temporal_context: Optional[str] = None
    affected_count: Optional[int] = None
    damage_severity: Optional[str] = None  # "minor" | "moderate" | "severe"


class Classification(BaseModel):
    """Service classification result."""
    service_code: str
    service_name: str
    department: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    alternative_classifications: List[Dict[str, Any]] = Field(default_factory=list)


class Prediction(BaseModel):
    """Resolution time prediction."""
    expected_resolution_days: float
    confidence_interval_90: Dict[str, float]
    factors: List[Dict[str, str]] = Field(default_factory=list)


class Reasoning(BaseModel):
    """Reasoning and explanation for triage decision."""
    classification_reasoning: str
    similar_requests: List[Dict[str, Any]] = Field(default_factory=list)
    data_sources_used: List[str] = Field(default_factory=list)


class TriageRequest(BaseModel):
    """Incoming triage request."""
    text: Optional[str] = None
    audio: Optional[str] = None  # Base64 encoded
    location: Optional[Location] = None
    user_context: Optional[Dict[str, Any]] = None


class TriageResponse(BaseModel):
    """Triage response with classification and prediction."""
    request_id: UUID = Field(default_factory=uuid4)
    user_summary: str
    extracted_entities: ExtractedEntities
    classification: Classification
    prediction: Prediction
    reasoning: Reasoning
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
