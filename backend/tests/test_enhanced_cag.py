"""
Tests for Enhanced CAG Agent with Specialized Critics
"""

import pytest
from app.agents.enhanced_cag_agent import (
    EnhancedCAGAgent,
    TechnicalAccuracyCritic,
    CompletenessCritic,
    SafetyCritic,
    ClarityCritic
)


@pytest.mark.unit
@pytest.mark.cag
class TestEnhancedCAGAgent:
    """Test Enhanced CAG Agent functionality"""

    @pytest.mark.asyncio
    async def test_cag_initialization(self, mock_llm_service):
        """Test CAG agent initialization"""
        agent = EnhancedCAGAgent(
            llm_service=mock_llm_service,
            config={
                'max_stages': 2,
                'confidence_target': 0.85
            }
        )

        assert agent is not None
        assert len(agent.critics) == 4
        assert 'technical_accuracy' in agent.critics
        assert 'completeness' in agent.critics
        assert 'safety' in agent.critics
        assert 'clarity' in agent.critics

    @pytest.mark.asyncio
    async def test_cag_improves_low_confidence(
        self,
        sample_incident,
        sample_rag_response,
        mock_llm_service
    ):
        """Test that CAG improves low confidence responses"""
        agent = EnhancedCAGAgent(
            llm_service=mock_llm_service,
            config={'max_stages': 2}
        )

        initial_confidence = sample_rag_response['confidence']
        assert initial_confidence < 0.7

        response = await agent.refine(
            incident=sample_incident,
            initial_response=sample_rag_response,
            initial_confidence=initial_confidence
        )

        # CAG should improve confidence
        assert response.final_confidence >= initial_confidence
        assert response.total_stages > 0
        assert len(response.stages) > 0

    @pytest.mark.asyncio
    async def test_critics_evaluation(self, sample_incident, sample_rag_response, mock_llm_service):
        """Test that all critics are evaluated"""
        agent = EnhancedCAGAgent(llm_service=mock_llm_service)

        evaluations = await agent._run_critics(sample_incident, sample_rag_response)

        assert len(evaluations) > 0
        # Check that different critic types are present
        critic_names = {e.critic_name for e in evaluations}
        assert len(critic_names) > 0

    @pytest.mark.asyncio
    async def test_consistency_verification(
        self,
        sample_incident,
        sample_rag_response,
        mock_llm_service
    ):
        """Test self-consistency verification"""
        agent = EnhancedCAGAgent(
            llm_service=mock_llm_service,
            config={'enable_consistency_verification': True}
        )

        consistency_score, alternatives = await agent._verify_consistency(
            incident=sample_incident,
            response=sample_rag_response,
            n_samples=2
        )

        assert 0.0 <= consistency_score <= 1.0
        assert isinstance(alternatives, list)

    @pytest.mark.asyncio
    async def test_cag_statistics(self, mock_llm_service):
        """Test CAG statistics collection"""
        agent = EnhancedCAGAgent(llm_service=mock_llm_service)

        stats = await agent.get_stats()

        assert 'total_refinements' in stats
        assert 'average_stages' in stats
        assert 'critic_statistics' in stats


@pytest.mark.unit
@pytest.mark.cag
class TestCritics:
    """Test individual critics"""

    @pytest.mark.asyncio
    async def test_technical_accuracy_critic(self, sample_incident, sample_rag_response, mock_llm_service):
        """Test technical accuracy critic"""
        critic = TechnicalAccuracyCritic(mock_llm_service)

        evaluation = await critic.evaluate(sample_incident, sample_rag_response)

        assert evaluation.critic_name == "technical_accuracy"
        assert 0.0 <= evaluation.score <= 1.0
        assert isinstance(evaluation.issues, list)
        assert isinstance(evaluation.suggestions, list)

    @pytest.mark.asyncio
    async def test_completeness_critic(self, sample_incident, sample_rag_response, mock_llm_service):
        """Test completeness critic"""
        critic = CompletenessCritic(mock_llm_service)

        evaluation = await critic.evaluate(sample_incident, sample_rag_response)

        assert evaluation.critic_name == "completeness"
        assert 0.0 <= evaluation.score <= 1.0

    @pytest.mark.asyncio
    async def test_safety_critic(self, sample_incident, sample_rag_response, mock_llm_service):
        """Test safety critic"""
        critic = SafetyCritic(mock_llm_service)

        evaluation = await critic.evaluate(sample_incident, sample_rag_response)

        assert evaluation.critic_name == "safety"
        assert evaluation.severity in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_clarity_critic(self, sample_incident, sample_rag_response, mock_llm_service):
        """Test clarity critic"""
        critic = ClarityCritic(mock_llm_service)

        evaluation = await critic.evaluate(sample_incident, sample_rag_response)

        assert evaluation.critic_name == "clarity"
        assert 0.0 <= evaluation.score <= 1.0
