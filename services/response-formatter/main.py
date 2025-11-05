"""
Response Formatter Service - Format final triage responses.
"""

from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime

from shared.models.request import (
    TriageResponse,
    ExtractedEntities,
    Classification,
    Prediction,
    Reasoning
)
from shared.models.prediction import PredictionResult
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class ResponseFormatter:
    """Format triage responses for API output."""

    async def format_response(
        self,
        user_input: str,
        entities: ExtractedEntities,
        classification: Classification,
        prediction: PredictionResult,
        context: Dict[str, Any],
        processing_time_ms: float
    ) -> TriageResponse:
        """
        Create a complete triage response.

        Args:
            user_input: Original user input
            entities: Extracted entities
            classification: LLM classification result
            prediction: ML prediction result
            context: Retrieved context from GraphRAG
            processing_time_ms: Total processing time

        Returns:
            Formatted TriageResponse
        """
        # Create user summary
        user_summary = self._create_summary(user_input, classification, prediction)

        # Format prediction
        prediction_dict = Prediction(
            expected_resolution_days=prediction.predicted_days,
            confidence_interval_90={
                "lower_bound": prediction.confidence_90_lower,
                "upper_bound": prediction.confidence_90_upper
            },
            factors=self._extract_factors(prediction, entities, context)
        )

        # Format reasoning
        reasoning_dict = Reasoning(
            classification_reasoning=self._create_classification_reasoning(
                classification,
                entities,
                context
            ),
            similar_requests=self._format_similar_requests(context),
            data_sources_used=context.get("data_sources", [])
        )

        response = TriageResponse(
            request_id=uuid4(),
            user_summary=user_summary,
            extracted_entities=entities,
            classification=classification,
            prediction=prediction_dict,
            reasoning=reasoning_dict,
            created_at=datetime.utcnow(),
            processing_time_ms=processing_time_ms
        )

        logger.info(
            "response_formatted",
            request_id=str(response.request_id),
            service=classification.service_code,
            predicted_days=prediction.predicted_days
        )

        return response

    def _create_summary(
        self,
        user_input: str,
        classification: Classification,
        prediction: PredictionResult
    ) -> str:
        """Create a user-friendly summary."""
        days = int(round(prediction.predicted_days))
        lower = int(round(prediction.confidence_90_lower))
        upper = int(round(prediction.confidence_90_upper))

        summary = (
            f"Your request has been classified as '{classification.service_name}' "
            f"and will be handled by the {classification.department} department. "
            f"Based on historical data, we estimate this will be resolved in approximately "
            f"{days} days (typically between {lower}-{upper} days). "
        )

        if classification.confidence_score >= 0.9:
            summary += "We are highly confident in this classification."
        elif classification.confidence_score >= 0.7:
            summary += "We are moderately confident in this classification."
        else:
            summary += "Please review the classification to ensure accuracy."

        return summary

    def _create_classification_reasoning(
        self,
        classification: Classification,
        entities: ExtractedEntities,
        context: Dict[str, Any]
    ) -> str:
        """Create detailed reasoning for classification."""
        reasons = []

        # Keywords match
        if entities.service_keywords:
            reasons.append(
                f"Request mentions key terms: {', '.join(entities.service_keywords[:3])}"
            )

        # Similar requests
        similar = context.get("similar_requests", [])
        if similar:
            matching_service = sum(
                1 for req in similar
                if req.get("service_type") == classification.service_code
            )
            if matching_service > 0:
                reasons.append(
                    f"{matching_service} out of {len(similar)} similar historical requests "
                    f"were classified as {classification.service_name}"
                )

        # Location context
        if entities.location and entities.location.neighborhood:
            reasons.append(
                f"Request is in {entities.location.neighborhood} neighborhood"
            )

        # Urgency
        if entities.urgency_indicators:
            reasons.append(
                f"Urgency indicators detected: {', '.join(entities.urgency_indicators)}"
            )

        if not reasons:
            reasons.append(
                f"Classification based on standard routing rules for {classification.department}"
            )

        return ". ".join(reasons) + "."

    def _extract_factors(
        self,
        prediction: PredictionResult,
        entities: ExtractedEntities,
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract factors affecting prediction."""
        factors = []

        # Temporal factors
        now = datetime.utcnow()
        if now.weekday() >= 5:
            factors.append({
                "factor_name": "Weekend submission",
                "impact": "slows_down",
                "description": "Requests submitted on weekends typically take longer to process"
            })

        if now.month in [11, 12, 1]:  # Winter months
            factors.append({
                "factor_name": "Winter season",
                "impact": "slows_down",
                "description": "Higher volume of weather-related requests during winter"
            })

        # Urgency factors
        if entities.urgency_indicators:
            factors.append({
                "factor_name": "Urgent request",
                "impact": "speeds_up",
                "description": "Request marked as urgent may receive priority handling"
            })

        # Severity factors
        if entities.damage_severity == "severe":
            factors.append({
                "factor_name": "Severe damage",
                "impact": "speeds_up",
                "description": "Severe damage reports are typically prioritized"
            })
        elif entities.damage_severity == "minor":
            factors.append({
                "factor_name": "Minor issue",
                "impact": "neutral",
                "description": "Minor issues follow standard processing timelines"
            })

        # Historical factors
        similar = context.get("similar_requests", [])
        if similar:
            avg_days = prediction.features_used.get("similar_requests_avg", 0)
            if avg_days > 10:
                factors.append({
                    "factor_name": "Complex issue type",
                    "impact": "slows_down",
                    "description": f"Similar requests averaged {avg_days:.0f} days to resolve"
                })
            elif avg_days < 5:
                factors.append({
                    "factor_name": "Quick resolution type",
                    "impact": "speeds_up",
                    "description": f"Similar requests averaged {avg_days:.0f} days to resolve"
                })

        return factors

    def _format_similar_requests(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format similar requests for response."""
        similar = context.get("similar_requests", [])
        formatted = []

        for req in similar[:3]:  # Top 3 only
            formatted.append({
                "request_number": req.get("request_number"),
                "similarity_score": round(req.get("similarity_score", 0), 2),
                "resolution_days": req.get("resolution_days"),
                "service_type": req.get("service_type"),
                "description": req.get("text", "")[:100] + "..."
            })

        return formatted


if __name__ == "__main__":
    import asyncio

    async def test():
        formatter = ResponseFormatter()

        # Mock data
        from shared.models.request import ExtractedEntities, Classification
        from shared.models.prediction import PredictionResult

        entities = ExtractedEntities(
            service_keywords=["pothole", "road"],
            urgency_indicators=[],
            damage_severity="moderate"
        )

        classification = Classification(
            service_code="SDOT_POTHOLE",
            service_name="Pothole Repair",
            department="SDOT",
            confidence_score=0.92,
            alternative_classifications=[]
        )

        prediction = PredictionResult(
            predicted_days=7.5,
            confidence_90_lower=5.0,
            confidence_90_upper=10.0,
            prediction_std=2.0,
            model_version="1.0.0",
            features_used={"similar_requests_avg": 7.0}
        )

        context = {
            "similar_requests": [
                {
                    "request_number": "20-000001",
                    "text": "Pothole on main street",
                    "similarity_score": 0.89,
                    "resolution_days": 6,
                    "service_type": "SDOT_POTHOLE"
                }
            ],
            "data_sources": ["vector_similarity", "graph_relationships"]
        }

        response = await formatter.format_response(
            user_input="There's a pothole on 5th Avenue",
            entities=entities,
            classification=classification,
            prediction=prediction,
            context=context,
            processing_time_ms=250.5
        )

        print("\nFormatted Response:")
        print(f"Request ID: {response.request_id}")
        print(f"Summary: {response.user_summary}")
        print(f"Service: {response.classification.service_name}")
        print(f"Predicted days: {response.prediction.expected_resolution_days}")
        print(f"Factors affecting prediction: {len(response.prediction.factors)}")

    asyncio.run(test())
