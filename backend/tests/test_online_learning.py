"""
Tests for Online Learning Pipeline
"""

import pytest
from datetime import datetime
from app.learning.online_learning import (
    OnlineLearningPipeline,
    FeedbackRecord,
    PerformanceRecord,
    ContextualBandit
)


@pytest.mark.unit
class TestOnlineLearningPipeline:
    """Test Online Learning Pipeline"""

    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = OnlineLearningPipeline(config={'adaptation_threshold': 5})

        assert pipeline.adaptation_threshold == 5
        assert len(pipeline.feedback_buffer) == 0
        assert len(pipeline.performance_buffer) == 0

    @pytest.mark.asyncio
    async def test_record_feedback(self):
        """Test recording feedback"""
        pipeline = OnlineLearningPipeline()

        feedback = FeedbackRecord(
            incident_id="test-001",
            recommendation_id="rec-001",
            feedback_type="positive",
            rating=4.5
        )

        await pipeline.record_feedback(feedback)

        assert len(pipeline.feedback_buffer) == 1
        assert pipeline.stats['total_feedback'] == 1
        assert pipeline.stats['positive_feedback'] == 1

    @pytest.mark.asyncio
    async def test_record_performance(self):
        """Test recording performance"""
        pipeline = OnlineLearningPipeline()

        performance = PerformanceRecord(
            incident_id="test-001",
            agent_type="rag",
            processing_time=1.5,
            confidence=0.85,
            success=True
        )

        await pipeline.record_performance(performance)

        assert len(pipeline.performance_buffer) == 1

    @pytest.mark.asyncio
    async def test_adaptation_threshold(self, sample_feedback_records):
        """Test adaptation is triggered at threshold"""
        pipeline = OnlineLearningPipeline(config={'adaptation_threshold': 3})

        # Add feedback records
        for record_data in sample_feedback_records:
            feedback = FeedbackRecord(**record_data)
            await pipeline.record_feedback(feedback)

        # Adaptation should have been triggered
        assert len(pipeline.feedback_buffer) >= 3

    def test_get_current_parameters(self):
        """Test getting current adaptive parameters"""
        pipeline = OnlineLearningPipeline()

        params = pipeline.get_current_parameters()

        assert 'ranking_weights' in params
        assert 'cag_thresholds' in params
        assert 'learning_rate' in params

    def test_get_statistics(self):
        """Test getting pipeline statistics"""
        pipeline = OnlineLearningPipeline()

        stats = pipeline.get_statistics()

        assert 'status' in stats
        assert 'statistics' in stats
        assert 'current_parameters' in stats


@pytest.mark.unit
class TestContextualBandit:
    """Test Contextual Bandit for strategy selection"""

    def test_bandit_initialization(self):
        """Test bandit initialization"""
        strategies = ['direct_rag', 'rag_with_cag', 'multi_agent']
        bandit = ContextualBandit(strategies)

        assert len(bandit.strategies) == 3
        assert all(strategy in bandit.alpha for strategy in strategies)
        assert all(strategy in bandit.beta for strategy in strategies)

    def test_strategy_selection(self):
        """Test strategy selection"""
        strategies = ['strategy_a', 'strategy_b', 'strategy_c']
        bandit = ContextualBandit(strategies)

        selected = bandit.select_strategy()

        assert selected in strategies

    def test_bandit_update(self):
        """Test bandit update with reward"""
        strategies = ['strategy_a', 'strategy_b']
        bandit = ContextualBandit(strategies)

        initial_alpha = bandit.alpha['strategy_a']
        initial_beta = bandit.beta['strategy_a']

        # Update with reward
        bandit.update('strategy_a', reward=1.0)

        assert bandit.alpha['strategy_a'] > initial_alpha
        assert bandit.beta['strategy_a'] == initial_beta

    def test_bandit_statistics(self):
        """Test bandit statistics"""
        strategies = ['strategy_a', 'strategy_b']
        bandit = ContextualBandit(strategies)

        # Perform some selections and updates
        for _ in range(5):
            strategy = bandit.select_strategy()
            bandit.update(strategy, reward=0.8)

        stats = bandit.get_statistics()

        assert 'strategy_a' in stats
        assert 'strategy_b' in stats
        assert all('pulls' in stats[s] for s in strategies)
        assert all('expected_value' in stats[s] for s in strategies)
