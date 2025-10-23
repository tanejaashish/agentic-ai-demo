"""
Online Learning Pipeline
Continuous learning and adaptation from user feedback and system performance
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedbackRecord:
    """Record of user feedback"""
    incident_id: str
    recommendation_id: str
    feedback_type: str  # positive, negative, neutral
    rating: Optional[float] = None  # 0-5 scale
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceRecord:
    """Record of system performance"""
    incident_id: str
    agent_type: str  # rag, cag, predictor
    processing_time: float
    confidence: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningSignal:
    """Signal for learning adaptation"""
    signal_type: str  # embedding_update, ranking_adjust, threshold_change
    component: str
    adjustment: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class OnlineLearningPipeline:
    """
    Continuous learning pipeline that adapts system based on:
    - User feedback
    - Performance metrics
    - Error patterns
    - Usage patterns
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Feedback buffer
        self.feedback_buffer: deque[FeedbackRecord] = deque(
            maxlen=self.config.get('max_feedback_buffer', 1000)
        )

        # Performance buffer
        self.performance_buffer: deque[PerformanceRecord] = deque(
            maxlen=self.config.get('max_performance_buffer', 1000)
        )

        # Learning signals
        self.learning_signals: List[LearningSignal] = []

        # Adaptation thresholds
        self.adaptation_threshold = self.config.get('adaptation_threshold', 10)
        self.learning_rate = self.config.get('learning_rate', 0.1)

        # Component weights (for adaptive ranking)
        self.ranking_weights = {
            'semantic_similarity': 0.5,
            'keyword_match': 0.3,
            'recency': 0.1,
            'popularity': 0.1
        }

        # CAG thresholds (adaptive)
        self.cag_thresholds = {
            'confidence_target': 0.85,
            'refinement_trigger': 0.7,
            'max_iterations': 3
        }

        # Statistics
        self.stats = {
            'total_feedback': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'adaptations_made': 0,
            'last_adaptation': None
        }

        # Background task
        self.learning_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info("Online Learning Pipeline initialized")

    async def start(self):
        """Start the online learning background task"""
        if not self.running:
            self.running = True
            self.learning_task = asyncio.create_task(self._continuous_learning_loop())
            logger.info("Online learning pipeline started")

    async def stop(self):
        """Stop the online learning background task"""
        self.running = False
        if self.learning_task:
            self.learning_task.cancel()
            try:
                await self.learning_task
            except asyncio.CancelledError:
                pass
        logger.info("Online learning pipeline stopped")

    async def record_feedback(self, feedback: FeedbackRecord):
        """Record user feedback"""
        self.feedback_buffer.append(feedback)
        self.stats['total_feedback'] += 1

        if feedback.feedback_type == 'positive':
            self.stats['positive_feedback'] += 1
        elif feedback.feedback_type == 'negative':
            self.stats['negative_feedback'] += 1

        logger.info(
            f"Feedback recorded: {feedback.feedback_type} for incident {feedback.incident_id}"
        )

        # Immediate adaptation for critical negative feedback
        if feedback.feedback_type == 'negative' and feedback.rating and feedback.rating < 2.0:
            await self._immediate_adaptation(feedback)

    async def record_performance(self, performance: PerformanceRecord):
        """Record system performance"""
        self.performance_buffer.append(performance)

        logger.debug(
            f"Performance recorded: {performance.agent_type} "
            f"for incident {performance.incident_id} "
            f"(time: {performance.processing_time:.2f}s, success: {performance.success})"
        )

    async def _continuous_learning_loop(self):
        """Main continuous learning loop"""
        while self.running:
            try:
                # Check if we have enough data to adapt
                if len(self.feedback_buffer) >= self.adaptation_threshold:
                    await self._perform_adaptation()

                # Sleep for configured interval (default: 5 minutes)
                interval = self.config.get('learning_interval_seconds', 300)
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _perform_adaptation(self):
        """Perform learning adaptation based on collected data"""
        logger.info(
            f"Performing adaptation with {len(self.feedback_buffer)} feedback records "
            f"and {len(self.performance_buffer)} performance records"
        )

        # 1. Update ranking weights based on feedback
        await self._update_ranking_weights()

        # 2. Adapt CAG thresholds based on performance
        await self._adapt_cag_thresholds()

        # 3. Identify and learn from error patterns
        await self._learn_from_errors()

        # 4. Update embedding priorities (simulate)
        await self._update_embedding_priorities()

        # Record adaptation
        self.stats['adaptations_made'] += 1
        self.stats['last_adaptation'] = datetime.now()

        logger.info(f"Adaptation complete. Total adaptations: {self.stats['adaptations_made']}")

    async def _update_ranking_weights(self):
        """Update ranking weights based on feedback"""
        # Analyze which ranking factors correlate with positive feedback
        positive_feedback = [
            f for f in self.feedback_buffer
            if f.feedback_type == 'positive'
        ]

        if len(positive_feedback) < 5:
            return  # Not enough data

        # Simple adaptation: boost semantic similarity if positive feedback rate is high
        positive_rate = len(positive_feedback) / len(self.feedback_buffer)

        if positive_rate > 0.7:
            # Good performance, slightly increase semantic weight
            self.ranking_weights['semantic_similarity'] = min(
                0.7,
                self.ranking_weights['semantic_similarity'] + self.learning_rate * 0.1
            )

            signal = LearningSignal(
                signal_type="ranking_adjust",
                component="ranking_weights",
                adjustment={"semantic_similarity": self.ranking_weights['semantic_similarity']},
                confidence=positive_rate
            )
            self.learning_signals.append(signal)

            logger.info(
                f"Ranking weights updated: semantic_similarity = "
                f"{self.ranking_weights['semantic_similarity']:.3f}"
            )

        elif positive_rate < 0.4:
            # Poor performance, adjust weights
            self.ranking_weights['keyword_match'] = min(
                0.5,
                self.ranking_weights['keyword_match'] + self.learning_rate * 0.1
            )

            signal = LearningSignal(
                signal_type="ranking_adjust",
                component="ranking_weights",
                adjustment={"keyword_match": self.ranking_weights['keyword_match']},
                confidence=1.0 - positive_rate
            )
            self.learning_signals.append(signal)

            logger.info(
                f"Ranking weights updated: keyword_match = "
                f"{self.ranking_weights['keyword_match']:.3f}"
            )

    async def _adapt_cag_thresholds(self):
        """Adapt CAG refinement thresholds based on performance"""
        # Analyze CAG performance
        cag_performances = [
            p for p in self.performance_buffer
            if p.agent_type == 'cag'
        ]

        if len(cag_performances) < 5:
            return

        # Calculate average metrics
        avg_confidence = np.mean([p.confidence for p in cag_performances])
        avg_time = np.mean([p.processing_time for p in cag_performances])
        success_rate = sum(p.success for p in cag_performances) / len(cag_performances)

        # Adapt confidence target
        if success_rate > 0.8 and avg_confidence > 0.85:
            # System performing well, can raise the bar
            self.cag_thresholds['confidence_target'] = min(
                0.95,
                self.cag_thresholds['confidence_target'] + 0.02
            )

            logger.info(
                f"CAG confidence target raised to {self.cag_thresholds['confidence_target']:.2f}"
            )

        elif success_rate < 0.6:
            # System struggling, lower threshold
            self.cag_thresholds['confidence_target'] = max(
                0.75,
                self.cag_thresholds['confidence_target'] - 0.02
            )

            logger.info(
                f"CAG confidence target lowered to {self.cag_thresholds['confidence_target']:.2f}"
            )

        # Adapt max iterations based on processing time
        if avg_time > 10.0:  # Too slow
            self.cag_thresholds['max_iterations'] = max(
                1,
                self.cag_thresholds['max_iterations'] - 1
            )

            logger.info(
                f"CAG max iterations reduced to {self.cag_thresholds['max_iterations']}"
            )

        signal = LearningSignal(
            signal_type="threshold_change",
            component="cag_thresholds",
            adjustment=self.cag_thresholds.copy(),
            confidence=success_rate
        )
        self.learning_signals.append(signal)

    async def _learn_from_errors(self):
        """Identify and learn from error patterns"""
        # Get failed performances
        failures = [
            p for p in self.performance_buffer
            if not p.success
        ]

        if not failures:
            return

        # Group failures by agent type
        failure_by_agent = defaultdict(list)
        for failure in failures:
            failure_by_agent[failure.agent_type].append(failure)

        # Log patterns
        for agent_type, agent_failures in failure_by_agent.items():
            failure_rate = len(agent_failures) / len([
                p for p in self.performance_buffer
                if p.agent_type == agent_type
            ])

            if failure_rate > 0.2:  # More than 20% failure rate
                logger.warning(
                    f"High failure rate detected for {agent_type}: {failure_rate:.1%}"
                )

                # Create signal for monitoring/alerting
                signal = LearningSignal(
                    signal_type="error_pattern",
                    component=agent_type,
                    adjustment={"failure_rate": failure_rate},
                    confidence=1.0
                )
                self.learning_signals.append(signal)

    async def _update_embedding_priorities(self):
        """Update embedding model priorities based on feedback"""
        # This is a simulated update - in production, would trigger
        # actual embedding model fine-tuning or weight updates

        positive_feedback = [
            f for f in self.feedback_buffer
            if f.feedback_type == 'positive'
        ]

        if len(positive_feedback) >= self.adaptation_threshold:
            # Extract successful query patterns
            successful_patterns = {}

            logger.info(
                f"Collected {len(positive_feedback)} positive feedback samples "
                "for embedding optimization"
            )

            signal = LearningSignal(
                signal_type="embedding_update",
                component="vector_embeddings",
                adjustment={"samples_collected": len(positive_feedback)},
                confidence=0.8
            )
            self.learning_signals.append(signal)

    async def _immediate_adaptation(self, feedback: FeedbackRecord):
        """Perform immediate adaptation for critical negative feedback"""
        logger.warning(
            f"Critical negative feedback received for incident {feedback.incident_id}, "
            "performing immediate adaptation"
        )

        # Lower confidence thresholds temporarily
        self.cag_thresholds['refinement_trigger'] = max(
            0.5,
            self.cag_thresholds['refinement_trigger'] - 0.05
        )

        signal = LearningSignal(
            signal_type="immediate_adjustment",
            component="cag_thresholds",
            adjustment={"refinement_trigger": self.cag_thresholds['refinement_trigger']},
            confidence=1.0
        )
        self.learning_signals.append(signal)

    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current adaptive parameters"""
        return {
            "ranking_weights": self.ranking_weights.copy(),
            "cag_thresholds": self.cag_thresholds.copy(),
            "learning_rate": self.learning_rate,
            "adaptation_threshold": self.adaptation_threshold
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning pipeline statistics"""
        feedback_rate = (
            self.stats['positive_feedback'] / max(self.stats['total_feedback'], 1)
        )

        recent_signals = self.learning_signals[-10:]

        return {
            "status": "running" if self.running else "stopped",
            "statistics": self.stats.copy(),
            "feedback_rate": feedback_rate,
            "buffer_sizes": {
                "feedback": len(self.feedback_buffer),
                "performance": len(self.performance_buffer)
            },
            "current_parameters": self.get_current_parameters(),
            "recent_learning_signals": [
                {
                    "type": s.signal_type,
                    "component": s.component,
                    "confidence": s.confidence,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in recent_signals
            ]
        }

    async def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for analysis"""
        return {
            "timestamp": datetime.now().isoformat(),
            "feedback_records": [
                {
                    "incident_id": f.incident_id,
                    "feedback_type": f.feedback_type,
                    "rating": f.rating,
                    "timestamp": f.timestamp.isoformat()
                }
                for f in list(self.feedback_buffer)[-100:]
            ],
            "performance_records": [
                {
                    "agent_type": p.agent_type,
                    "processing_time": p.processing_time,
                    "confidence": p.confidence,
                    "success": p.success,
                    "timestamp": p.timestamp.isoformat()
                }
                for p in list(self.performance_buffer)[-100:]
            ],
            "learning_signals": [
                {
                    "signal_type": s.signal_type,
                    "component": s.component,
                    "adjustment": s.adjustment,
                    "confidence": s.confidence,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in self.learning_signals[-50:]
            ],
            "statistics": self.get_statistics()
        }


class ContextualBandit:
    """
    Contextual bandit for strategy selection
    Uses Thompson sampling to select optimal strategy based on context
    """

    def __init__(self, strategies: List[str]):
        self.strategies = strategies

        # Beta distribution parameters for each strategy
        self.alpha = {strategy: 1.0 for strategy in strategies}
        self.beta = {strategy: 1.0 for strategy in strategies}

        # Rewards history
        self.rewards_history = {strategy: [] for strategy in strategies}

        logger.info(f"Contextual Bandit initialized with strategies: {strategies}")

    def select_strategy(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Select strategy using Thompson sampling

        Args:
            context: Context features for contextual bandit (optional)

        Returns:
            Selected strategy name
        """
        # Sample from beta distribution for each strategy
        samples = {}
        for strategy in self.strategies:
            samples[strategy] = np.random.beta(
                self.alpha[strategy],
                self.beta[strategy]
            )

        # Select strategy with highest sample
        selected_strategy = max(samples.items(), key=lambda x: x[1])[0]

        logger.debug(f"Strategy selected: {selected_strategy} (samples: {samples})")
        return selected_strategy

    def update(self, strategy: str, reward: float):
        """
        Update bandit with reward for selected strategy

        Args:
            strategy: Strategy that was used
            reward: Reward received (0-1 scale, 1 = success)
        """
        # Update beta distribution parameters
        self.alpha[strategy] += reward
        self.beta[strategy] += (1 - reward)

        # Record reward
        self.rewards_history[strategy].append(reward)

        logger.debug(
            f"Bandit updated: {strategy} with reward {reward:.2f} "
            f"(α={self.alpha[strategy]:.1f}, β={self.beta[strategy]:.1f})"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics"""
        stats = {}

        for strategy in self.strategies:
            rewards = self.rewards_history[strategy]

            if rewards:
                stats[strategy] = {
                    "pulls": len(rewards),
                    "avg_reward": np.mean(rewards),
                    "success_rate": sum(r > 0.5 for r in rewards) / len(rewards),
                    "alpha": self.alpha[strategy],
                    "beta": self.beta[strategy],
                    "expected_value": self.alpha[strategy] / (
                        self.alpha[strategy] + self.beta[strategy]
                    )
                }
            else:
                stats[strategy] = {
                    "pulls": 0,
                    "avg_reward": 0.0,
                    "success_rate": 0.0,
                    "alpha": self.alpha[strategy],
                    "beta": self.beta[strategy],
                    "expected_value": 0.5
                }

        return stats


# Global online learning pipeline instance
_global_pipeline: Optional[OnlineLearningPipeline] = None


def get_learning_pipeline() -> OnlineLearningPipeline:
    """Get or create global learning pipeline"""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = OnlineLearningPipeline()
    return _global_pipeline
