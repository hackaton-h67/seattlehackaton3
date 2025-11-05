"""
ML Prediction Service - Predict resolution times using ensemble models.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from shared.models.request import ExtractedEntities
from shared.models.prediction import PredictionResult
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class MLPredictionService:
    """Ensemble ML model for resolution time prediction."""

    def __init__(self):
        self.models = {}
        self.ensemble_weights = None
        self.model_version = "1.0.0"

        if settings.enable_ml_prediction:
            self._load_models()
        else:
            logger.warning("ml_prediction_disabled_by_config")

    def _load_models(self):
        """Load trained models from disk."""
        model_path = Path(settings.ml_model_path)

        if not model_path.exists():
            logger.warning("model_path_not_found", path=str(model_path))
            return

        try:
            # Load individual models
            model_files = ["linear", "random_forest", "gradient_boost", "neural_net"]
            loaded_count = 0

            for model_name in model_files:
                model_file = model_path / f"{model_name}.joblib"
                if model_file.exists():
                    self.models[model_name] = joblib.load(model_file)
                    loaded_count += 1
                    logger.info("model_loaded", model=model_name)

            # Load ensemble weights
            weights_file = model_path / "ensemble_weights.joblib"
            if weights_file.exists():
                self.ensemble_weights = joblib.load(weights_file)
            else:
                # Equal weights if not found
                self.ensemble_weights = {name: 0.25 for name in model_files}

            logger.info("ml_models_loaded", count=loaded_count)

        except Exception as e:
            logger.error("model_loading_failed", error=str(e))
            self.models = {}

    async def predict_resolution_time(
        self,
        service_code: str,
        department: str,
        entities: ExtractedEntities,
        similar_requests: list = None
    ) -> PredictionResult:
        """
        Predict resolution time with confidence intervals.

        Args:
            service_code: Classified service code
            department: Department handling the request
            entities: Extracted entities
            similar_requests: Similar historical requests (optional)

        Returns:
            PredictionResult with prediction and confidence intervals
        """
        if not self.models:
            # Use fallback prediction based on similar requests
            return self._fallback_prediction(similar_requests)

        try:
            # Engineer features
            features = self._engineer_features(
                service_code,
                department,
                entities,
                similar_requests
            )

            # Make predictions with all models
            predictions = []
            for model_name, model in self.models.items():
                pred = model.predict([features])[0]
                weight = self.ensemble_weights.get(model_name, 0.25)
                predictions.append(pred * weight)

            # Ensemble prediction
            mean_prediction = np.sum(predictions)
            std_prediction = np.std(predictions)

            # Confidence intervals (90%)
            confidence_lower = max(1.0, mean_prediction - 1.645 * std_prediction)
            confidence_upper = mean_prediction + 1.645 * std_prediction

            result = PredictionResult(
                predicted_days=float(mean_prediction),
                confidence_90_lower=float(confidence_lower),
                confidence_90_upper=float(confidence_upper),
                prediction_std=float(std_prediction),
                model_version=self.model_version,
                features_used={
                    "service_code": service_code,
                    "department": department,
                    "has_location": entities.location is not None,
                    "urgency_count": len(entities.urgency_indicators),
                    "similar_requests_avg": self._calculate_similar_avg(similar_requests)
                }
            )

            logger.info(
                "prediction_made",
                service=service_code,
                predicted_days=mean_prediction,
                confidence_range=f"{confidence_lower:.1f}-{confidence_upper:.1f}"
            )

            return result

        except Exception as e:
            logger.error("prediction_failed", error=str(e))
            return self._fallback_prediction(similar_requests)

    def _engineer_features(
        self,
        service_code: str,
        department: str,
        entities: ExtractedEntities,
        similar_requests: list = None
    ) -> np.ndarray:
        """
        Engineer features for ML model.

        Returns feature vector matching training format.
        """
        now = datetime.utcnow()

        # Service and department encoding (simplified - use label encoding in production)
        service_hash = hash(service_code) % 100
        dept_hash = hash(department) % 20

        # Temporal features
        month = now.month
        day_of_week = now.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Location features
        has_location = 1 if entities.location else 0
        council_district = 0  # Would extract from location
        neighborhood_density = 5  # Would look up

        # Urgency and severity
        urgency_count = len(entities.urgency_indicators)
        severity_map = {"minor": 1, "moderate": 2, "severe": 3}
        severity_score = severity_map.get(entities.damage_severity, 0)

        # Historical features
        similar_avg = self._calculate_similar_avg(similar_requests)

        # Create feature vector (10 features to match training)
        features = np.array([
            service_hash,
            dept_hash,
            month,
            day_of_week,
            is_weekend,
            has_location,
            urgency_count,
            severity_score,
            similar_avg,
            neighborhood_density
        ], dtype=float)

        return features

    def _calculate_similar_avg(self, similar_requests: list = None) -> float:
        """Calculate average resolution time from similar requests."""
        if not similar_requests:
            return 7.0  # Default fallback

        resolution_times = [
            req.get("resolution_days")
            for req in similar_requests
            if req.get("resolution_days") is not None
        ]

        if resolution_times:
            return float(np.mean(resolution_times))

        return 7.0

    def _fallback_prediction(self, similar_requests: list = None) -> PredictionResult:
        """Fallback prediction when models are unavailable."""
        if similar_requests:
            similar_avg = self._calculate_similar_avg(similar_requests)
            std = 3.0  # Assumed standard deviation

            return PredictionResult(
                predicted_days=similar_avg,
                confidence_90_lower=max(1.0, similar_avg - 1.645 * std),
                confidence_90_upper=similar_avg + 1.645 * std,
                prediction_std=std,
                model_version="fallback",
                features_used={"method": "similar_requests_average"}
            )

        # Ultimate fallback - use default
        return PredictionResult(
            predicted_days=7.0,
            confidence_90_lower=3.0,
            confidence_90_upper=14.0,
            prediction_std=4.0,
            model_version="fallback",
            features_used={"method": "default"}
        )


if __name__ == "__main__":
    import asyncio

    async def test():
        service = MLPredictionService()

        from shared.models.request import ExtractedEntities

        # Test prediction
        entities = ExtractedEntities(
            service_keywords=["pothole"],
            urgency_indicators=[],
            damage_severity="moderate"
        )

        result = await service.predict_resolution_time(
            service_code="SDOT_POTHOLE",
            department="SDOT",
            entities=entities,
            similar_requests=[
                {"resolution_days": 5},
                {"resolution_days": 7},
                {"resolution_days": 10}
            ]
        )

        print(f"\nPrediction:")
        print(f"  Predicted days: {result.predicted_days:.1f}")
        print(f"  90% CI: {result.confidence_90_lower:.1f} - {result.confidence_90_upper:.1f}")
        print(f"  Std dev: {result.prediction_std:.1f}")
        print(f"  Model version: {result.model_version}")

    asyncio.run(test())
