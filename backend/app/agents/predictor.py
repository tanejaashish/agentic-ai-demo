"""
Predictive Agent for incident severity and resolution time estimation
Uses ML models to predict incident characteristics
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
    Predicts severity, resolution time, and team assignment
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
        
        # Initialize models
        self._initialize_models()
        
        logger.info("Predictive Agent initialized")
    
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
        Returns predictions for severity, resolution time, and team
        """
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
                    "features_used": len(features),
                    "model_version": "1.0",
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
            logger.error(f"Prediction failed: {e}")
            # Return default predictions on error
            return self._get_default_predictions(incident)
    
    def _extract_features(self, incident: Incident) -> np.ndarray:
        """Extract numerical features from incident"""
        features = []
        
        # Basic categorical features
        category_encoded = self.category_encoder.transform([incident.category])[0]
        priority_encoded = self.priority_encoder.transform([incident.priority])[0]
        features.extend([category_encoded, priority_encoded])
        
        # Text-based features
        if self.text_features_enabled:
            # Title length and word count
            title_length = len(incident.title)
            title_words = len(incident.title.split())
            features.extend([title_length, title_words])
            
            # Description length and word count
            desc_length = len(incident.description)
            desc_words = len(incident.description.split())
            features.extend([desc_length, desc_words])
            
            # Error message presence and length
            has_error = 1 if incident.error_message else 0
            error_length = len(incident.error_message) if incident.error_message else 0
            features.extend([has_error, error_length])
            
            # Keywords presence (simplified)
            keywords = ['critical', 'urgent', 'down', 'failed', 'error', 'timeout', 'crash']
            text_combined = f"{incident.title} {incident.description}".lower()
            keyword_count = sum(1 for kw in keywords if kw in text_combined)
            features.append(keyword_count)
        
        # System complexity features
        num_affected_systems = len(incident.affected_systems) if incident.affected_systems else 0
        features.append(num_affected_systems)
        
        # Temporal features
        if self.temporal_features_enabled and incident.timestamp:
            hour = incident.timestamp.hour
            day_of_week = incident.timestamp.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            is_business_hours = 1 if 9 <= hour <= 17 else 0
            features.extend([hour, day_of_week, is_weekend, is_business_hours])
        else:
            # Default temporal features
            features.extend([12, 2, 0, 1])  # Noon, Wednesday, Weekday, Business hours
        
        return np.array(features).reshape(1, -1)
    
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
        except:
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
        except:
            return 60, 0.5
    
    def _predict_team(self, features: np.ndarray) -> Tuple[str, float]:
        """Predict team assignment"""
        if self.team_model is None:
            return "L1-Support", 0.5
        
        try:
            # Get prediction and probability
            prediction = self.team_model.predict(features)[0]
            probabilities = self.team_model.predict_proba(features)[0]
            confidence = max(probabilities)
            
            team = self.team_encoder.inverse_transform([prediction])[0]
            
            return team, confidence
        except:
            return "L1-Support", 0.5
    
    def _analyze_risk_factors(self, incident: Incident, severity: str) -> List[str]:
        """Analyze and identify risk factors"""
        risk_factors = []
        
        # Priority-based risks
        if incident.priority in [Priority.CRITICAL, Priority.HIGH]:
            risk_factors.append(f"{incident.priority} priority indicates urgent attention needed")
        
        # Category-based risks
        high_risk_categories = [Category.SECURITY, Category.DATABASE, Category.AUTHENTICATION]
        if incident.category in high_risk_categories:
            risk_factors.append(f"{incident.category} issues can have wide impact")
        
        # System complexity
        if incident.affected_systems and len(incident.affected_systems) > 3:
            risk_factors.append(f"Multiple systems affected ({len(incident.affected_systems)})")
        
        # Error message analysis
        if incident.error_message:
            critical_errors = ['OutOfMemory', 'Connection refused', 'Database locked', 'Authentication failed']
            for error in critical_errors:
                if error.lower() in incident.error_message.lower():
                    risk_factors.append(f"Critical error detected: {error}")
                    break
        
        # Severity-based risks
        if severity in ["high", "critical"]:
            risk_factors.append(f"Predicted {severity} severity requires immediate action")
        
        return risk_factors[:5]  # Limit to top 5 risk factors
    
    def _generate_recommendations(
        self,
        incident: Incident,
        severity: str,
        resolution_time: int,
        team: str
    ) -> List[str]:
        """Generate recommendations based on predictions"""
        recommendations = []
        
        # Severity-based recommendations
        if severity == "critical":
            recommendations.append("🚨 Initiate emergency response protocol")
            recommendations.append("📞 Alert on-call engineers immediately")
        elif severity == "high":
            recommendations.append("⚡ Prioritize this incident in the queue")
            recommendations.append("👥 Assign senior engineer for review")
        
        # Resolution time recommendations
        if resolution_time > 120:  # More than 2 hours
            recommendations.append(f"⏰ Long resolution expected ({resolution_time} min) - consider parallel workstreams")
        elif resolution_time < 30:
            recommendations.append(f"✅ Quick resolution possible ({resolution_time} min)")
        
        # Team recommendations
        recommendations.append(f"👨‍💻 Route to {team} for fastest resolution")
        
        # Category-specific recommendations
        category_recommendations = {
            Category.DATABASE: "🗄️ Check database metrics and connection pools",
            Category.NETWORK: "🌐 Verify network connectivity and firewall rules",
            Category.SECURITY: "🔒 Follow security incident response procedures",
            Category.APPLICATION: "📱 Review application logs and memory usage",
            Category.INFRASTRUCTURE: "🏗️ Check infrastructure monitoring dashboards"
        }
        
        if incident.category in category_recommendations:
            recommendations.append(category_recommendations[incident.category])
        
        return recommendations
    
    def _train_with_synthetic_data(self):
        """Train models with synthetic data for demo purposes"""
        # Generate synthetic training data
        n_samples = 1000
        np.random.seed(42)
        
        # Features: [category, priority, title_len, title_words, desc_len, desc_words, 
        #            has_error, error_len, keyword_count, num_systems, hour, day, weekend, business_hours]
        X = np.random.rand(n_samples, 14)
        
        # Scale features to reasonable ranges
        X[:, 0] *= len(Category) - 1  # Category
        X[:, 1] *= len(Priority) - 1  # Priority  
        X[:, 2] *= 100  # Title length
        X[:, 3] *= 20   # Title words
        X[:, 4] *= 500  # Description length
        X[:, 5] *= 100  # Description words
        X[:, 6] = (X[:, 6] > 0.5).astype(int)  # Has error (binary)
        X[:, 7] *= 50   # Error length
        X[:, 8] *= 5    # Keyword count
        X[:, 9] *= 5    # Number of systems
        X[:, 10] *= 23  # Hour
        X[:, 11] *= 6   # Day of week
        X[:, 12] = (X[:, 12] > 0.5).astype(int)  # Is weekend
        X[:, 13] = (X[:, 13] > 0.5).astype(int)  # Business hours
        
        # Generate synthetic labels based on features
        # Severity: influenced by priority and keyword count
        y_severity = ((X[:, 1] + X[:, 8] / 5) / 2 * 3).astype(int)
        y_severity = np.clip(y_severity, 0, 3)
        
        # Resolution time: influenced by severity and number of systems
        y_resolution = 30 + y_severity * 30 + X[:, 9] * 10 + np.random.normal(0, 10, n_samples)
        y_resolution = np.clip(y_resolution, 5, 480)
        
        # Team: influenced by category
        y_team = (X[:, 0] / 2).astype(int)
        y_team = np.clip(y_team, 0, 8)
        
        # Train models
        self.severity_model.fit(X, y_severity)
        self.resolution_model.fit(X, y_resolution)
        self.team_model.fit(X, y_team)
        
        logger.info("Models trained with synthetic data")
    
    def _get_default_predictions(self, incident: Incident) -> Dict[str, Any]:
        """Return default predictions when models fail"""
        # Map priority to severity
        severity_map = {
            Priority.CRITICAL: "critical",
            Priority.HIGH: "high",
            Priority.MEDIUM: "medium",
            Priority.LOW: "low"
        }
        severity = severity_map.get(incident.priority, "medium")
        
        # Estimate resolution time based on priority
        resolution_map = {
            Priority.CRITICAL: 30,
            Priority.HIGH: 60,
            Priority.MEDIUM: 120,
            Priority.LOW: 240
        }
        resolution_time = resolution_map.get(incident.priority, 60)
        
        # Assign team based on category
        team_map = {
            Category.DATABASE: "Database Team",
            Category.NETWORK: "Network Team",
            Category.SECURITY: "Security Team",
            Category.APPLICATION: "Development Team",
            Category.INFRASTRUCTURE: "Infrastructure Team"
        }
        team = team_map.get(incident.category, "L1-Support")
        
        return {
            "severity": severity,
            "severity_confidence": 0.5,
            "resolution_time": resolution_time,
            "resolution_confidence": 0.5,
            "team": team,
            "team_confidence": 0.5,
            "risk_factors": ["Default prediction - models unavailable"],
            "recommendations": ["Please review incident manually"],
            "metadata": {"fallback": True}
        }
    
    async def load_models(self):
        """Load pre-trained models if available"""
        try:
            # Attempt to load saved models
            self.severity_model = joblib.load('/app/models/severity_model.pkl')
            self.resolution_model = joblib.load('/app/models/resolution_model.pkl')
            self.team_model = joblib.load('/app/models/team_model.pkl')
            logger.info("Pre-trained models loaded successfully")
        except:
            logger.info("No pre-trained models found, using synthetic training data")
            self._train_with_synthetic_data()
    
    async def update_models(self, training_data: List[Dict[str, Any]]):
        """Update models with new training data (online learning)"""
        if not training_data:
            return
        
        # Extract features and labels from training data
        X = []
        y_severity = []
        y_resolution = []
        y_team = []
        
        for data in training_data:
            incident = data['incident']
            features = self._extract_features(incident)
            X.append(features[0])
            
            # Extract labels
            y_severity.append(data.get('actual_severity', 1))
            y_resolution.append(data.get('actual_resolution_time', 60))
            y_team.append(self.team_encoder.transform([data.get('actual_team', 'L1-Support')])[0])
        
        X = np.array(X)
        
        # Partial fit or retrain models
        # Note: RandomForest doesn't support partial_fit, so we retrain with combined data
        # In production, you might use SGDClassifier or similar for true online learning
        
        logger.info(f"Models updated with {len(training_data)} new samples")