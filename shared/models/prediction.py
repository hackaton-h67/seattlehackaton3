"""
ML prediction models.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfidenceInterval(BaseModel):
    """Confidence interval for predictions."""
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.90


class PredictionResult(BaseModel):
    """Machine learning prediction result."""
    predicted_days: float
    confidence_90_lower: float
    confidence_90_upper: float
    prediction_std: float
    model_version: str
    features_used: Dict[str, Any] = Field(default_factory=dict)
