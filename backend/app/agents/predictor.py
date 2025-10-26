"""
Predictive Agent for incident severity and resolution time estimation
FIXED v2: Correct 14-feature configuration (removed duplicate temporal features)
"""

import asyncio
import json
import pickle
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import logging
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

from app.models.incident import Incident, Priority, Category

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result from predictive analysis"""
    severity: str
    severity_confidence: float
    resolution_time: int  # in minutes
    resolution_confidence: float
    assigned_team: str
    team_confidence: float
    risk_factors: List[str]
    recommendations: List[str]
    prediction_metadata: Dict[str, Any]

class PredictiveAgent:
    """
    Predictive Agent for incident analysis
    FIXED v2: 14-feature configuration matching training
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model placeholders
        self.severity_model = None
        self.resolution_model = None
        self.team_model = None
        
        # Encoders for categorical variables
        self.category_encoder = LabelEncoder()
        self.priority_encoder = LabelEncoder()
        self.team_encoder = LabelEncoder()
        
        # Feature engineering parameters
        self.text_features_enabled = self.config.get('text_features', True)
        self.temporal_features_enabled = self.config.get('temporal_features', True)
        
        # FIXED: Set to 14 features (removed duplicate temporal features)
        self.n_features = 14
        
        # Initialize models
        self._initialize_models()
        
        logger.info("Predictive Agent initialized with 14 features")
    
    def _initialize_models(self):
        """Initialize ML models with default parameters"""
        # Severity prediction (multi-class classification)
        self.severity_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Resolution time prediction (regression)
        self.resolution_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Team assignment (multi-class classification)
        self.team_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        
        # Initialize encoders with default categories
        self.category_encoder.fit([cat.value for cat in Category])
        self.priority_encoder.fit([pri.value for pri in Priority])
        self.team_encoder.fit([
            "L1-Support", "L2-Support", "L3-Support",
            "Database Team", "Network Team", "Security Team",
            "Development Team", "Platform Team", "Infrastructure Team"
        ])
        
        # Train with synthetic data if no saved models exist
        self._train_with_synthetic_data()
    
    async def predict(self, incident: Incident) -> Dict[str, Any]:
        """
        Main prediction method
        FIXED: Better error handling and timeout
        """
        try:
            # FIXED: Add timeout to prevent hanging
            result = await asyncio.wait_for(
                self._do_predict(incident),
                timeout=5.0  # 5 second timeout for predictions
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("Prediction timed out, using defaults")
            return self._get_default_prediction(incident)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._get_default_prediction(incident)
    
    async def _do_predict(self, incident: Incident) -> Dict[str, Any]:
        """Internal prediction method"""
        try:
            # Extract features from incident
            features = self._extract_features(incident)
            
            # Make predictions
            severity_pred, severity_conf = self._predict_severity(features)
            resolution_pred, resolution_conf = self._predict_resolution_time(features)
            team_pred, team_conf = self._predict_team(features)
            
            # Analyze risk factors
            risk_factors = self._analyze_risk_factors(incident, severity_pred)
            
            # Generate recommendations based on predictions
            recommendations = self._generate_recommendations(
                incident, severity_pred, resolution_pred, team_pred
            )
            
            # Prepare result
            result = PredictionResult(
                severity=severity_pred,
                severity_confidence=severity_conf,
                resolution_time=resolution_pred,
                resolution_confidence=resolution_conf,
                assigned_team=team_pred,
                team_confidence=team_conf,
                risk_factors=risk_factors,
                recommendations=recommendations,
                prediction_metadata={
                    "features_used": len(features[0]),
                    "model_version": "1.1",
                    "prediction_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Predictions completed: Severity={severity_pred}, Resolution={resolution_pred}min, Team={team_pred}")
            
            # Return as dictionary for API response
            return {
                "severity": result.severity,
                "severity_confidence": result.severity_confidence,
                "resolution_time": result.resolution_time,
                "resolution_confidence": result.resolution_confidence,
                "team": result.assigned_team,
                "team_confidence": result.team_confidence,
                "risk_factors": result.risk_factors,
                "recommendations": result.recommendations,
                "metadata": result.prediction_metadata
            }
        except Exception as e:
            logger.error(f"Prediction error in _do_predict: {e}")
            return self._get_default_prediction(incident)
    
    def _extract_features(self, incident: Incident) -> np.ndarray:
        """
        Extract numerical features from incident
        FIXED v2: Returns exactly 14 features
        
        Feature breakdown:
        0: category_encoded
        1: priority_encoded
        2: title_length
        3: title_words
        4: desc_length
        5: desc_words
        6: has_error
        7: error_length
        8: keyword_count
        9: num_affected_systems
        10: hour
        11: day_of_week
        12: is_weekend
        13: is_business_hours
        """
        features = []
        
        try:
            # FIXED: Convert enum to string value before encoding
            category_str = incident.category.value if hasattr(incident.category, 'value') else str(incident.category)
            priority_str = incident.priority.value if hasattr(incident.priority, 'value') else str(incident.priority)
            
            # Handle if category/priority might not be in encoder
            try:
                category_encoded = self.category_encoder.transform([category_str])[0]
            except ValueError:
                logger.warning(f"Unknown category: {category_str}, using default")
                category_encoded = 0
            
            try:
                priority_encoded = self.priority_encoder.transform([priority_str])[0]
            except ValueError:
                logger.warning(f"Unknown priority: {priority_str}, using default")
                priority_encoded = 1  # Default to Medium
            
            # Features 0-1: Category and priority
            features.extend([category_encoded, priority_encoded])
            
            # Features 2-3: Title features
            title_length = len(incident.title)
            title_words = len(incident.title.split())
            features.extend([title_length, title_words])
            
            # Features 4-5: Description features
            desc_length = len(incident.description)
            desc_words = len(incident.description.split())
            features.extend([desc_length, desc_words])
            
            # Features 6-7: Error message features
            has_error = 1 if incident.error_message else 0
            error_length = len(incident.error_message) if incident.error_message else 0
            features.extend([has_error, error_length])
            
            # Feature 8: Keywords presence (simplified)
            keywords = ['critical', 'urgent', 'down', 'failed', 'error', 'timeout', 'crash']
            text_combined = f"{incident.title} {incident.description}".lower()
            keyword_count = sum(1 for kw in keywords if kw in text_combined)
            features.append(keyword_count)
            
            # Feature 9: System complexity features
            num_affected_systems = len(incident.affected_systems) if incident.affected_systems else 0
            features.append(num_affected_systems)
            
            # Features 10-13: Temporal features (FIXED: No duplicates)
            if incident.timestamp:
                hour = incident.timestamp.hour
                day_of_week = incident.timestamp.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                is_business_hours = 1 if 9 <= hour <= 17 else 0
                features.extend([hour, day_of_week, is_weekend, is_business_hours])
            else:
                # Default temporal features
                features.extend([12, 2, 0, 1])  # Noon, Wednesday, Weekday, Business hours
            
            # CRITICAL: Ensure exactly 14 features
            result = np.array(features).reshape(1, -1)
            if result.shape[1] != 14:
                logger.error(f"Feature count mismatch! Expected 14, got {result.shape[1]}")
                # Pad or truncate to 14
                if result.shape[1] < 14:
                    padding = np.zeros((1, 14 - result.shape[1]))
                    result = np.hstack([result, padding])
                else:
                    result = result[:, :14]
            
            return result
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return default feature vector of exactly 14 features
            return np.zeros((1, 14))
    
    def _predict_severity(self, features: np.ndarray) -> Tuple[str, float]:
        """Predict incident severity"""
        if self.severity_model is None:
            return "medium", 0.5
        
        try:
            # Get prediction and probability
            prediction = self.severity_model.predict(features)[0]
            probabilities = self.severity_model.predict_proba(features)[0]
            confidence = max(probabilities)
            
            severity_mapping = {0: "low", 1: "medium", 2: "high", 3: "critical"}
            severity = severity_mapping.get(prediction, "medium")
            
            return severity, confidence
        except Exception as e:
            logger.error(f"Severity prediction error: {e}")
            return "medium", 0.5
    
    def _predict_resolution_time(self, features: np.ndarray) -> Tuple[int, float]:
        """Predict resolution time in minutes"""
        if self.resolution_model is None:
            return 60, 0.5
        
        try:
            # Predict time
            prediction = self.resolution_model.predict(features)[0]
            
            # Ensure reasonable bounds (5 minutes to 8 hours)
            resolution_time = max(5, min(480, int(prediction)))
            
            # Estimate confidence based on feature importance
            confidence = 0.7  # Simplified confidence calculation
            
            return resolution_time, confidence
        except Exception as e:
            logger.error(f"Resolution time prediction error: {e}")
            return 60, 0.5
    
    def _predict_team(self, features: np.ndarray) -> Tuple[str, float]:
        """Predict team assignment"""
        if self.team_model is None:
            return "L1-Support", 0.5
        
        try:
            # Get prediction
            prediction = self.team_model.predict(features)[0]
            probabilities = self.team_model.predict_proba(features)[0]
            confidence = max(probabilities)
            
            # Decode team
            team = self.team_encoder.inverse_transform([prediction])[0]
            
            return team, confidence
        except Exception as e:
            logger.error(f"Team prediction error: {e}")
            return "L1-Support", 0.5
    
    def _analyze_risk_factors(self, incident: Incident, severity: str) -> List[str]:
        """Analyze risk factors for the incident"""
        risk_factors = []
        
        # Check severity
        if severity in ["high", "critical"]:
            risk_factors.append("High severity incident requiring immediate attention")
        
        # Check affected systems
        if incident.affected_systems and len(incident.affected_systems) > 3:
            risk_factors.append("Multiple systems affected - potential widespread impact")
        
        # Check for critical keywords
        text = f"{incident.title} {incident.description}".lower()
        if "production" in text or "prod" in text:
            risk_factors.append("Production environment affected")
        if "customer" in text or "client" in text:
            risk_factors.append("Customer-facing service impacted")
        if "data" in text and ("loss" in text or "corrupt" in text):
            risk_factors.append("Potential data integrity issue")
        
        # Time-based risk
        if incident.timestamp:
            hour = incident.timestamp.hour
            if hour < 6 or hour > 22:
                risk_factors.append("Outside business hours - limited support available")
        
        return risk_factors
    
    def _generate_recommendations(
        self, 
        incident: Incident, 
        severity: str, 
        resolution_time: int, 
        team: str
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Severity-based recommendations
        if severity == "critical":
            recommendations.append("Initiate emergency response procedure")
            recommendations.append("Notify incident commander immediately")
        elif severity == "high":
            recommendations.append("Escalate to senior team members")
            recommendations.append("Set up war room if needed")
        
        # Time-based recommendations
        if resolution_time > 120:
            recommendations.append("Prepare stakeholder communication")
            recommendations.append("Consider workaround solutions")
        
        # Team-based recommendations
        if "L1" not in team:
            recommendations.append(f"Assign to {team} for specialized handling")
        
        # Add monitoring recommendation
        recommendations.append("Set up continuous monitoring")
        
        return recommendations
    
    def _get_default_prediction(self, incident: Incident) -> Dict[str, Any]:
        """Return default prediction when model fails"""
        # Extract category for better defaults
        category_str = incident.category.value if hasattr(incident.category, 'value') else str(incident.category)
        
        # Set defaults based on category
        if "DATABASE" in category_str.upper():
            severity = "high"
            resolution_time = 90
            team = "Database Team"
        elif "NETWORK" in category_str.upper():
            severity = "high"
            resolution_time = 60
            team = "Network Team"
        elif "SECURITY" in category_str.upper():
            severity = "critical"
            resolution_time = 45
            team = "Security Team"
        else:
            severity = "medium"
            resolution_time = 60
            team = "L1-Support"
        
        return {
            "severity": severity,
            "severity_confidence": 0.5,
            "resolution_time": resolution_time,
            "resolution_confidence": 0.5,
            "team": team,
            "team_confidence": 0.5,
            "risk_factors": ["Prediction service unavailable - using defaults"],
            "recommendations": ["Manual assessment recommended"],
            "metadata": {
                "fallback_mode": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _train_with_synthetic_data(self):
        """Train models with synthetic data for demo"""
        try:
            # Generate synthetic training data with EXACTLY 14 features
            n_samples = 1000
            n_features = 14  # FIXED: Match feature extraction
            
            # Random features
            X = np.random.randn(n_samples, n_features)
            
            # Synthetic labels for severity (0-3)
            y_severity = np.random.randint(0, 4, n_samples)
            
            # Synthetic labels for resolution time (5-480 minutes)
            y_resolution = np.random.randint(5, 480, n_samples)
            
            # Synthetic labels for team (0-8)
            y_team = np.random.randint(0, 9, n_samples)
            
            # Train models
            self.severity_model.fit(X, y_severity)
            self.resolution_model.fit(X, y_resolution)
            self.team_model.fit(X, y_team)
            
            logger.info(f"Models trained with synthetic data (14 features)")
        except Exception as e:
            logger.error(f"Failed to train with synthetic data: {e}")
    
    async def load_models(self):
        """Load pre-trained models if available"""
        try:
            # Check if saved models exist
            # For now, just use synthetic data
            logger.info("Predictive models loaded")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def save_models(self, path: str = "/app/models"):
        """Save trained models"""
        try:
            import os
            os.makedirs(path, exist_ok=True)
            
            joblib.dump(self.severity_model, f"{path}/severity_model.pkl")
            joblib.dump(self.resolution_model, f"{path}/resolution_model.pkl")
            joblib.dump(self.team_model, f"{path}/team_model.pkl")
            
            logger.info(f"Models saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")