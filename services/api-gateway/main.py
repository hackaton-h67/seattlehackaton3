"""
API Gateway - Main entry point for Service-Sense.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time
import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent
sys.path.insert(0, str(services_path))

from shared.config.settings import settings
from shared.models.request import TriageRequest, TriageResponse
from shared.utils.logging import setup_logging, get_logger
from shared.utils.metrics import MetricsCollector

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Metrics
metrics = MetricsCollector()

# Initialize services
input_processor = None
entity_extractor = None
graphrag_orchestrator = None
llm_triage = None
ml_prediction = None
response_formatter = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Startup and shutdown events."""
    global input_processor, entity_extractor, graphrag_orchestrator
    global llm_triage, ml_prediction, response_formatter

    logger.info("starting_api_gateway", version="2.0.0")

    # Initialize all services
    try:
        from input_processor.main import InputProcessor
        from entity_extraction.main import EntityExtractor
        from graphrag_orchestrator.main import GraphRAGOrchestrator
        from llm_triage.main import LLMTriageService
        from ml_prediction.main import MLPredictionService
        from response_formatter.main import ResponseFormatter

        input_processor = InputProcessor()
        entity_extractor = EntityExtractor()
        graphrag_orchestrator = GraphRAGOrchestrator()
        llm_triage = LLMTriageService()
        ml_prediction = MLPredictionService()
        response_formatter = ResponseFormatter()

        logger.info("all_services_initialized")
    except Exception as e:
        logger.error("service_initialization_failed", error=str(e))
        logger.warning("some_services_may_not_be_available")

    yield

    logger.info("shutting_down_api_gateway")


app = FastAPI(
    title="Service-Sense API",
    version="2.0.0",
    description="Intelligent Triage & Predictive Resolution System",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track metrics for each request."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    metrics.record_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    )
    metrics.record_response_time(
        endpoint=request.url.path,
        duration=duration
    )

    response.headers["X-Process-Time"] = str(duration)
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Service-Sense API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.post("/api/v2/triage", response_model=TriageResponse)
async def triage_request(request: TriageRequest) -> TriageResponse:
    """
    Triage a service request.

    This endpoint processes a citizen's service request (text or audio),
    classifies it to the correct service type and department, and predicts
    the resolution time.

    Args:
        request: Triage request with text/audio and optional location

    Returns:
        Complete triage response with classification and prediction
    """
    start_time = time.time()

    try:
        logger.info("processing_triage_request", has_audio=bool(request.audio))

        # Validate input
        if not request.text and not request.audio:
            raise HTTPException(
                status_code=400,
                detail="Either text or audio input is required"
            )

        # Step 1: Process input (text or audio)
        if request.audio and input_processor:
            processed = await input_processor.process(request.audio)
            user_text = processed.text
        else:
            user_text = request.text or ""

        # Step 2: Extract entities
        if entity_extractor:
            entities = await entity_extractor.extract(user_text, request.location)
        else:
            from shared.models.request import ExtractedEntities
            entities = ExtractedEntities(location=request.location)

        logger.info(
            "entities_extracted",
            keywords=len(entities.service_keywords),
            has_location=entities.location is not None
        )

        # Step 3: Retrieve context using GraphRAG
        context = {}
        if graphrag_orchestrator:
            context = await graphrag_orchestrator.retrieve_context(user_text, entities)
            context_text = graphrag_orchestrator.format_context_for_llm(context)
        else:
            context_text = ""

        # Step 4: Classify with LLM
        if llm_triage:
            classification = await llm_triage.classify(user_text, entities, context_text)
        else:
            from shared.models.request import Classification
            classification = Classification(
                service_code="GENERAL",
                service_name="General Service Request",
                department="CUSTOMER_SERVICE",
                confidence_score=0.5
            )

        logger.info(
            "classification_complete",
            service=classification.service_code,
            confidence=classification.confidence_score
        )

        # Step 5: Predict resolution time
        if ml_prediction:
            prediction = await ml_prediction.predict_resolution_time(
                service_code=classification.service_code,
                department=classification.department,
                entities=entities,
                similar_requests=context.get("similar_requests", [])
            )
        else:
            from shared.models.prediction import PredictionResult
            prediction = PredictionResult(
                predicted_days=7.0,
                confidence_90_lower=3.0,
                confidence_90_upper=14.0,
                prediction_std=4.0,
                model_version="fallback",
                features_used={}
            )

        logger.info(
            "prediction_complete",
            predicted_days=prediction.predicted_days
        )

        # Step 6: Format response
        processing_time = (time.time() - start_time) * 1000

        if response_formatter:
            response = await response_formatter.format_response(
                user_input=user_text,
                entities=entities,
                classification=classification,
                prediction=prediction,
                context=context,
                processing_time_ms=processing_time
            )
        else:
            # Fallback response formatting
            from shared.models.request import Prediction, Reasoning
            response = TriageResponse(
                user_summary=f"Request classified as {classification.service_name}",
                extracted_entities=entities,
                classification=classification,
                prediction=Prediction(
                    expected_resolution_days=prediction.predicted_days,
                    confidence_interval_90={
                        "lower_bound": prediction.confidence_90_lower,
                        "upper_bound": prediction.confidence_90_upper
                    },
                    factors=[]
                ),
                reasoning=Reasoning(
                    classification_reasoning="Automated classification",
                    similar_requests=[],
                    data_sources_used=context.get("data_sources", [])
                ),
                processing_time_ms=processing_time
            )

        # Track metrics
        metrics.requests_by_department.labels(
            department=classification.department
        ).inc()

        metrics.requests_by_service.labels(
            service=classification.service_code
        ).inc()

        logger.info(
            "triage_completed",
            request_id=str(response.request_id),
            processing_time_ms=processing_time
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("triage_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/services")
async def list_services(department: str = None, category: str = None):
    """
    List all available service types.

    Args:
        department: Filter by department (optional)
        category: Filter by category (optional)

    Returns:
        List of service types
    """
    # TODO: Implement service listing from database
    return {
        "services": [],
        "total": 0
    }


@app.get("/api/v2/services/{service_code}/performance")
async def get_service_performance(service_code: str, timeframe: str = "month"):
    """
    Get historical performance metrics for a service.

    Args:
        service_code: Service type code
        timeframe: Time period (week, month, quarter, year)

    Returns:
        Performance metrics
    """
    # TODO: Implement performance metrics retrieval
    return {
        "service_code": service_code,
        "metrics": {}
    }


@app.post("/api/v2/feedback")
async def submit_feedback(feedback: dict):
    """
    Submit feedback on prediction accuracy.

    Args:
        feedback: Feedback data including request_number, actual resolution, rating

    Returns:
        Confirmation
    """
    # TODO: Implement feedback processing
    logger.info("feedback_received", request_number=feedback.get("request_number"))
    return {
        "status": "received",
        "message": "Thank you for your feedback"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
