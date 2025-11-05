#!/usr/bin/env python3
"""
Train ML models for resolution time prediction.

This script trains an ensemble of models for predicting service request
resolution times based on historical Seattle data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from pathlib import Path

from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


class ResolutionTimePredictor:
    """Ensemble model for predicting resolution times."""

    def __init__(self):
        self.models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boost': GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=8,
                random_state=42
            ),
            'neural_net': MLPRegressor(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                learning_rate_init=0.001,
                random_state=42,
                max_iter=500
            )
        }
        self.ensemble_weights = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train all models in the ensemble."""
        logger.info("training_models")

        predictions = {}

        for name, model in self.models.items():
            logger.info("training_model", model=name)
            model.fit(X_train, y_train)

            # Evaluate on validation set
            val_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, val_pred)
            rmse = np.sqrt(mean_squared_error(y_val, val_pred))
            r2 = r2_score(y_val, val_pred)

            logger.info(
                "model_metrics",
                model=name,
                mae=round(mae, 2),
                rmse=round(rmse, 2),
                r2=round(r2, 3)
            )

            predictions[name] = val_pred

        # Learn optimal ensemble weights (for now, use equal weights)
        self.ensemble_weights = {name: 0.25 for name in self.models.keys()}

        logger.info("training_complete")

    def predict_with_confidence(self, X):
        """Make predictions with confidence intervals."""
        predictions = []

        for name, model in self.models.items():
            pred = model.predict(X)
            predictions.append(pred * self.ensemble_weights[name])

        mean_prediction = np.sum(predictions, axis=0)
        std_prediction = np.std(predictions, axis=0)

        return {
            'predicted_days': mean_prediction,
            'confidence_90_lower': mean_prediction - 1.645 * std_prediction,
            'confidence_90_upper': mean_prediction + 1.645 * std_prediction,
            'prediction_std': std_prediction
        }

    def save(self, path: str):
        """Save models to disk."""
        model_path = Path(path)
        model_path.mkdir(parents=True, exist_ok=True)

        for name, model in self.models.items():
            joblib.dump(model, model_path / f"{name}.joblib")

        joblib.dump(self.ensemble_weights, model_path / "ensemble_weights.joblib")
        logger.info("models_saved", path=path)


def main():
    """Main training pipeline."""
    logger.info("starting_model_training")

    # TODO: Load and preprocess data
    # For now, create dummy data
    logger.warning("using_dummy_data_for_demo")

    np.random.seed(42)
    n_samples = 1000

    X = np.random.randn(n_samples, 10)  # 10 features
    y = np.random.uniform(1, 30, n_samples)  # Resolution days 1-30

    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    # Train models
    predictor = ResolutionTimePredictor()
    predictor.train(X_train, y_train, X_val, y_val)

    # Test ensemble
    result = predictor.predict_with_confidence(X_test)
    mae = mean_absolute_error(y_test, result['predicted_days'])
    logger.info("ensemble_mae", mae=round(mae, 2))

    # Save models
    predictor.save(settings.ml_model_path)

    logger.info("training_complete")


if __name__ == "__main__":
    main()
