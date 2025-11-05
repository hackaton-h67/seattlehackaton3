"""
Metrics collection using Prometheus.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
from typing import Dict


class MetricsCollector:
    """Prometheus metrics collector."""

    def __init__(self) -> None:
        # System health metrics
        self.api_requests = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status']
        )

        self.api_response_time = Histogram(
            'api_response_time_seconds',
            'API response time in seconds',
            ['endpoint']
        )

        self.error_rate = Gauge(
            'error_rate',
            'Current error rate',
            ['service']
        )

        # Model performance metrics
        self.triage_accuracy = Gauge(
            'triage_accuracy',
            'Triage classification accuracy'
        )

        self.prediction_mae = Gauge(
            'prediction_mae_days',
            'Prediction mean absolute error in days'
        )

        self.confidence_calibration = Gauge(
            'confidence_calibration',
            'Percentage within confidence interval'
        )

        self.feedback_score = Gauge(
            'feedback_score',
            'Average user feedback score'
        )

        # Business metrics
        self.requests_by_department = Counter(
            'requests_by_department',
            'Requests by department',
            ['department']
        )

        self.requests_by_service = Counter(
            'requests_by_service',
            'Requests by service type',
            ['service']
        )

        self.transfer_rate = Gauge(
            'transfer_rate',
            'Rate of requests transferred between departments'
        )

    def record_request(self, method: str, endpoint: str, status: int) -> None:
        """Record API request."""
        self.api_requests.labels(method=method, endpoint=endpoint, status=status).inc()

    def record_response_time(self, endpoint: str, duration: float) -> None:
        """Record API response time."""
        self.api_response_time.labels(endpoint=endpoint).observe(duration)
