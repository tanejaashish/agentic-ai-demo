"""
Enhanced CAG (Corrective Augmented Generation) Agent with Specialized Critics
Multi-stage refinement with domain-specific critics and self-consistency verification
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import numpy as np
import logging
from abc import ABC, abstractmethod

from app.services.llm_service import LLMService
from app.models.incident import Incident
from app.utils.validation import ResponseValidator

logger = logging.getLogger(__name__)


@dataclass
class CriticEvaluation:
    """Result of a single critic's evaluation"""
    critic_name: str
    score: float  # 0-1 scale
    issues: List[str]
    suggestions: List[str]
    severity: str  # "low", "medium", "high", "critical"
    processing_time: float


@dataclass
class RefinerStage:
    """Single stage of multi-stage refinement"""
    stage_number: int
    stage_name: str
    input_response: Dict[str, Any]
    critic_evaluations: List[CriticEvaluation]
    corrections_applied: List[Dict[str, Any]]
    refined_response: Dict[str, Any]
    confidence_before: float
    confidence_after: float
    overall_health_score: float


@dataclass
class EnhancedCAGResponse:
    """Complete enhanced CAG response with multi-stage refinement"""
    final_recommendations: List[Dict[str, Any]]
    final_confidence: float
    stages: List[RefinerStage]
    total_stages: int
    improvement_percentage: float
    sources: List[Dict[str, Any]]
    consistency_score: float
    alternative_solutions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class BaseCritic(ABC):
    """Base class for all critics"""

    def __init__(self, llm_service: LLMService, weight: float = 1.0):
        self.llm_service = llm_service
        self.weight = weight
        self.evaluation_count = 0

    @abstractmethod
    async def evaluate(self, incident: Incident, response: Dict[str, Any]) -> CriticEvaluation:
        """Evaluate response and return critique"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get critic name"""
        pass


class TechnicalAccuracyCritic(BaseCritic):
    """Evaluates technical accuracy and correctness"""

    def get_name(self) -> str:
        return "technical_accuracy"

    async def evaluate(self, incident: Incident, response: Dict[str, Any]) -> CriticEvaluation:
        start_time = datetime.now()

        prompt = f"""
        As a technical accuracy expert, evaluate the following incident response for technical correctness.

        Incident Details:
        - Title: {incident.title}
        - Category: {incident.category}
        - Description: {incident.description}
        - Error Message: {incident.error_message or "N/A"}

        Response to Evaluate:
        {json.dumps(response.get('recommendations', [{}])[0] if response.get('recommendations') else {}, indent=2)}

        Evaluate for:
        1. Technical correctness of commands and procedures
        2. Accuracy of error diagnosis
        3. Validity of proposed solutions
        4. Correct use of technical terminology
        5. Alignment with best practices

        Provide your evaluation in JSON format:
        {{
            "score": <0-100>,
            "issues": ["issue1", "issue2"],
            "suggestions": ["suggestion1", "suggestion2"],
            "severity": "low|medium|high|critical"
        }}
        """

        result = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.2
        )

        try:
            eval_data = json.loads(result)
            score = float(eval_data.get('score', 70)) / 100
            issues = eval_data.get('issues', [])
            suggestions = eval_data.get('suggestions', [])
            severity = eval_data.get('severity', 'medium')
        except:
            score = 0.7
            issues = ["Could not parse technical evaluation"]
            suggestions = ["Review technical details manually"]
            severity = "medium"

        self.evaluation_count += 1
        processing_time = (datetime.now() - start_time).total_seconds()

        return CriticEvaluation(
            critic_name=self.get_name(),
            score=score,
            issues=issues,
            suggestions=suggestions,
            severity=severity,
            processing_time=processing_time
        )


class CompletenessCritic(BaseCritic):
    """Evaluates completeness and thoroughness"""

    def get_name(self) -> str:
        return "completeness"

    async def evaluate(self, incident: Incident, response: Dict[str, Any]) -> CriticEvaluation:
        start_time = datetime.now()

        prompt = f"""
        As a completeness expert, evaluate if the incident response is thorough and complete.

        Incident: {incident.title}
        Priority: {incident.priority}
        Systems: {', '.join(incident.affected_systems) if incident.affected_systems else 'N/A'}

        Response to Evaluate:
        {json.dumps(response.get('recommendations', []), indent=2)[:1000]}

        Check for:
        1. All aspects of the incident addressed
        2. Root cause analysis included
        3. Prevention measures provided
        4. Escalation path defined
        5. Verification steps included
        6. Rollback plan if applicable

        Provide evaluation in JSON format:
        {{
            "score": <0-100>,
            "issues": ["missing element 1", "missing element 2"],
            "suggestions": ["add suggestion 1", "add suggestion 2"],
            "severity": "low|medium|high|critical"
        }}
        """

        result = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.2
        )

        try:
            eval_data = json.loads(result)
            score = float(eval_data.get('score', 70)) / 100
            issues = eval_data.get('issues', [])
            suggestions = eval_data.get('suggestions', [])
            severity = eval_data.get('severity', 'medium')
        except:
            score = 0.7
            issues = ["Could not parse completeness evaluation"]
            suggestions = ["Review for missing elements"]
            severity = "medium"

        self.evaluation_count += 1
        processing_time = (datetime.now() - start_time).total_seconds()

        return CriticEvaluation(
            critic_name=self.get_name(),
            score=score,
            issues=issues,
            suggestions=suggestions,
            severity=severity,
            processing_time=processing_time
        )


class SafetyCritic(BaseCritic):
    """Evaluates safety and risk considerations"""

    def get_name(self) -> str:
        return "safety"

    async def evaluate(self, incident: Incident, response: Dict[str, Any]) -> CriticEvaluation:
        start_time = datetime.now()

        prompt = f"""
        As a safety and risk expert, evaluate the incident response for potential risks.

        Incident: {incident.title} (Priority: {incident.priority})

        Proposed Solution:
        {json.dumps(response.get('recommendations', [{}])[0] if response.get('recommendations') else {}, indent=2)}

        Evaluate for:
        1. Potential data loss risks
        2. System downtime implications
        3. Security vulnerabilities
        4. Impact on other systems
        5. User impact
        6. Reversibility of changes

        Provide evaluation in JSON format:
        {{
            "score": <0-100>,
            "issues": ["risk 1", "risk 2"],
            "suggestions": ["mitigation 1", "mitigation 2"],
            "severity": "low|medium|high|critical"
        }}
        """

        result = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.2
        )

        try:
            eval_data = json.loads(result)
            score = float(eval_data.get('score', 80)) / 100
            issues = eval_data.get('issues', [])
            suggestions = eval_data.get('suggestions', [])
            severity = eval_data.get('severity', 'low')
        except:
            score = 0.8
            issues = ["Could not parse safety evaluation"]
            suggestions = ["Review safety considerations manually"]
            severity = "low"

        self.evaluation_count += 1
        processing_time = (datetime.now() - start_time).total_seconds()

        return CriticEvaluation(
            critic_name=self.get_name(),
            score=score,
            issues=issues,
            suggestions=suggestions,
            severity=severity,
            processing_time=processing_time
        )


class ClarityCritic(BaseCritic):
    """Evaluates clarity and actionability"""

    def get_name(self) -> str:
        return "clarity"

    async def evaluate(self, incident: Incident, response: Dict[str, Any]) -> CriticEvaluation:
        start_time = datetime.now()

        prompt = f"""
        As a clarity expert, evaluate if the incident response is clear and actionable.

        Response to Evaluate:
        {json.dumps(response.get('recommendations', []), indent=2)[:1000]}

        Evaluate for:
        1. Clear step-by-step instructions
        2. Unambiguous language
        3. Proper formatting and structure
        4. Actionable recommendations
        5. Appropriate technical level for audience
        6. Examples where helpful

        Provide evaluation in JSON format:
        {{
            "score": <0-100>,
            "issues": ["clarity issue 1", "clarity issue 2"],
            "suggestions": ["clarity improvement 1", "clarity improvement 2"],
            "severity": "low|medium|high|critical"
        }}
        """

        result = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.2
        )

        try:
            eval_data = json.loads(result)
            score = float(eval_data.get('score', 75)) / 100
            issues = eval_data.get('issues', [])
            suggestions = eval_data.get('suggestions', [])
            severity = eval_data.get('severity', 'low')
        except:
            score = 0.75
            issues = ["Could not parse clarity evaluation"]
            suggestions = ["Review for clarity improvements"]
            severity = "low"

        self.evaluation_count += 1
        processing_time = (datetime.now() - start_time).total_seconds()

        return CriticEvaluation(
            critic_name=self.get_name(),
            score=score,
            issues=issues,
            suggestions=suggestions,
            severity=severity,
            processing_time=processing_time
        )


class EnhancedCAGAgent:
    """
    Enhanced CAG Agent with multiple specialized critics and self-consistency verification
    """

    def __init__(
        self,
        llm_service: LLMService,
        config: Optional[Dict] = None
    ):
        self.llm_service = llm_service
        self.validator = ResponseValidator()

        # Configuration
        self.config = config or {}
        self.max_stages = self.config.get('max_stages', 2)
        self.confidence_target = self.config.get('confidence_target', 0.85)
        self.enable_consistency_verification = self.config.get('enable_consistency_verification', True)
        self.n_alternatives = self.config.get('n_alternatives', 2)
        self.consistency_threshold = self.config.get('consistency_threshold', 0.7)

        # Initialize critics
        self.critics = self._initialize_critics()

        # Learning and metrics
        self.refinement_history = []
        self.critic_performance = {name: [] for name in self.critics.keys()}

        logger.info(f"Enhanced CAG Agent initialized with {len(self.critics)} critics")

    def _initialize_critics(self) -> Dict[str, BaseCritic]:
        """Initialize all specialized critics"""
        return {
            'technical_accuracy': TechnicalAccuracyCritic(
                self.llm_service,
                weight=self.config.get('technical_weight', 1.5)
            ),
            'completeness': CompletenessCritic(
                self.llm_service,
                weight=self.config.get('completeness_weight', 1.2)
            ),
            'safety': SafetyCritic(
                self.llm_service,
                weight=self.config.get('safety_weight', 1.3)
            ),
            'clarity': ClarityCritic(
                self.llm_service,
                weight=self.config.get('clarity_weight', 1.0)
            )
        }

    async def refine(
        self,
        incident: Incident,
        initial_response: Dict[str, Any],
        initial_confidence: float
    ) -> EnhancedCAGResponse:
        """
        Main refinement method with multi-stage critic-based refinement
        """
        start_time = datetime.now()
        stages = []
        current_response = initial_response
        current_confidence = initial_confidence

        logger.info(f"Starting enhanced CAG refinement with {self.max_stages} stages")

        for stage_num in range(self.max_stages):
            stage_name = f"Stage {stage_num + 1}: Multi-Critic Evaluation"
            logger.info(f"{stage_name} - Current confidence: {current_confidence:.2f}")

            # Run all critics in parallel
            critic_evaluations = await self._run_critics(incident, current_response)

            # Calculate overall health score
            health_score = self._calculate_health_score(critic_evaluations)

            # Check if refinement is needed
            if health_score >= self.confidence_target and current_confidence >= self.confidence_target:
                logger.info(f"Target quality achieved: health={health_score:.2f}, confidence={current_confidence:.2f}")
                break

            # Apply targeted corrections based on critic feedback
            corrections, refined_response = await self._apply_targeted_corrections(
                incident,
                current_response,
                critic_evaluations
            )

            # Calculate new confidence
            new_confidence = self._calculate_refined_confidence(
                current_confidence,
                health_score,
                critic_evaluations
            )

            # Record stage
            stage = RefinerStage(
                stage_number=stage_num + 1,
                stage_name=stage_name,
                input_response=current_response,
                critic_evaluations=critic_evaluations,
                corrections_applied=corrections,
                refined_response=refined_response,
                confidence_before=current_confidence,
                confidence_after=new_confidence,
                overall_health_score=health_score
            )
            stages.append(stage)

            # Update for next iteration
            current_response = refined_response
            current_confidence = new_confidence

            # Check convergence
            if abs(new_confidence - current_confidence) < 0.01:
                logger.info("Convergence reached")
                break

        # Self-consistency verification
        consistency_score = 1.0
        alternatives = []
        if self.enable_consistency_verification:
            consistency_score, alternatives = await self._verify_consistency(
                incident,
                current_response,
                n_samples=self.n_alternatives
            )

            # If consistency is low, merge consistent parts
            if consistency_score < self.consistency_threshold:
                logger.info(f"Low consistency ({consistency_score:.2f}), merging alternatives")
                current_response = await self._merge_consistent_parts(
                    current_response,
                    alternatives
                )

        # Calculate improvement
        improvement = ((current_confidence - initial_confidence) / initial_confidence) * 100 if initial_confidence > 0 else 0

        # Build final response
        response = EnhancedCAGResponse(
            final_recommendations=current_response.get('recommendations', []),
            final_confidence=current_confidence,
            stages=stages,
            total_stages=len(stages),
            improvement_percentage=improvement,
            sources=initial_response.get('sources', []),
            consistency_score=consistency_score,
            alternative_solutions=alternatives,
            metadata={
                "initial_confidence": initial_confidence,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "critics_used": list(self.critics.keys()),
                "converged": current_confidence >= self.confidence_target,
                "consistency_verified": self.enable_consistency_verification,
                "cag_config": self.config
            }
        )

        # Update learning
        await self._update_learning(incident, response)

        logger.info(
            f"Enhanced CAG complete: {len(stages)} stages, "
            f"{improvement:.1f}% improvement, "
            f"consistency={consistency_score:.2f}"
        )

        return response

    async def _run_critics(
        self,
        incident: Incident,
        response: Dict[str, Any]
    ) -> List[CriticEvaluation]:
        """Run all critics in parallel"""
        tasks = [
            critic.evaluate(incident, response)
            for critic in self.critics.values()
        ]

        evaluations = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_evaluations = [
            e for e in evaluations
            if isinstance(e, CriticEvaluation)
        ]

        logger.info(f"Completed {len(valid_evaluations)}/{len(self.critics)} critic evaluations")
        return valid_evaluations

    def _calculate_health_score(self, evaluations: List[CriticEvaluation]) -> float:
        """Calculate overall health score from critic evaluations"""
        if not evaluations:
            return 0.5

        weighted_scores = []
        total_weight = 0

        for evaluation in evaluations:
            critic = self.critics.get(evaluation.critic_name)
            if critic:
                weight = critic.weight
                # Apply severity penalty
                severity_multiplier = {
                    'low': 1.0,
                    'medium': 0.9,
                    'high': 0.7,
                    'critical': 0.5
                }.get(evaluation.severity, 0.8)

                weighted_scores.append(evaluation.score * weight * severity_multiplier)
                total_weight += weight

        health_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.5
        return min(max(health_score, 0.0), 1.0)

    async def _apply_targeted_corrections(
        self,
        incident: Incident,
        response: Dict[str, Any],
        evaluations: List[CriticEvaluation]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply corrections based on critic feedback"""
        corrections = []

        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []
        for eval in evaluations:
            all_issues.extend([
                f"[{eval.critic_name}] {issue}"
                for issue in eval.issues
            ])
            all_suggestions.extend([
                f"[{eval.critic_name}] {sug}"
                for sug in eval.suggestions
            ])

        # Generate comprehensive correction
        correction_prompt = f"""
        Improve the following incident response based on expert feedback.

        Incident: {incident.title}
        Description: {incident.description}

        Current Response:
        {json.dumps(response.get('recommendations', []), indent=2)[:1500]}

        Issues Identified:
        {chr(10).join(all_issues[:10])}

        Improvement Suggestions:
        {chr(10).join(all_suggestions[:10])}

        Provide an improved response maintaining the same JSON structure.
        Focus on addressing the most critical issues first.
        """

        refined = await self.llm_service.generate(
            prompt=correction_prompt,
            max_tokens=1500,
            temperature=0.3
        )

        try:
            refined_response = json.loads(refined)
            corrections.append({
                "type": "comprehensive_refinement",
                "issues_addressed": len(all_issues),
                "suggestions_applied": len(all_suggestions)
            })
        except:
            refined_response = response
            logger.warning("Failed to parse refined response, using original")

        return corrections, refined_response

    def _calculate_refined_confidence(
        self,
        current_confidence: float,
        health_score: float,
        evaluations: List[CriticEvaluation]
    ) -> float:
        """Calculate new confidence score"""
        # Weighted combination of factors
        new_confidence = (
            0.3 * current_confidence +  # Preserve some of original
            0.5 * health_score +         # Primary factor: critic health score
            0.2 * (1 - self._calculate_issue_penalty(evaluations))  # Penalty for issues
        )

        return min(max(new_confidence, 0.0), 1.0)

    def _calculate_issue_penalty(self, evaluations: List[CriticEvaluation]) -> float:
        """Calculate penalty based on number and severity of issues"""
        total_issues = sum(len(e.issues) for e in evaluations)
        critical_issues = sum(
            len(e.issues) for e in evaluations
            if e.severity == 'critical'
        )

        penalty = (total_issues * 0.05) + (critical_issues * 0.15)
        return min(penalty, 0.5)  # Cap at 50% penalty

    async def _verify_consistency(
        self,
        incident: Incident,
        response: Dict[str, Any],
        n_samples: int = 2
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Verify self-consistency by generating alternative solutions"""
        logger.info(f"Generating {n_samples} alternative solutions for consistency check")

        prompt_base = f"""
        Provide a solution for the following incident:

        Title: {incident.title}
        Description: {incident.description}
        Priority: {incident.priority}
        Category: {incident.category}

        Provide a detailed technical solution with specific steps.
        """

        # Generate alternatives in parallel
        tasks = [
            self.llm_service.generate(
                prompt=prompt_base,
                max_tokens=800,
                temperature=0.7  # Higher temperature for diversity
            )
            for _ in range(n_samples)
        ]

        alternative_texts = await asyncio.gather(*tasks, return_exceptions=True)

        alternatives = []
        for i, alt_text in enumerate(alternative_texts):
            if not isinstance(alt_text, Exception):
                alternatives.append({
                    "alternative_id": i + 1,
                    "solution": alt_text,
                    "source": "self_consistency_verification"
                })

        # Calculate consistency score
        consistency_score = await self._compute_consistency_score(
            response,
            alternatives
        )

        return consistency_score, alternatives

    async def _compute_consistency_score(
        self,
        primary: Dict[str, Any],
        alternatives: List[Dict[str, Any]]
    ) -> float:
        """Compute consistency score between primary and alternative solutions"""
        if not alternatives:
            return 1.0

        # Use LLM to assess similarity
        alt_texts = "\n\n".join([
            f"Alternative {a['alternative_id']}: {a['solution'][:300]}"
            for a in alternatives
        ])

        prompt = f"""
        Compare the following solutions and rate their consistency (0-100).
        Consider if they address the same root cause and suggest similar approaches.

        Primary Solution:
        {json.dumps(primary.get('recommendations', [{}])[0] if primary.get('recommendations') else {}, indent=2)[:500]}

        Alternative Solutions:
        {alt_texts}

        Return only a numeric score (0-100):
        """

        score_text = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=10,
            temperature=0.1
        )

        try:
            score = float(score_text.strip()) / 100
        except:
            score = 0.7  # Default moderate consistency

        return min(max(score, 0.0), 1.0)

    async def _merge_consistent_parts(
        self,
        primary: Dict[str, Any],
        alternatives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge consistent parts from alternatives into primary"""
        alt_solutions = "\n".join([
            alt['solution'][:300]
            for alt in alternatives
        ])

        prompt = f"""
        Merge the following solutions, keeping the consistent elements and
        strengthening the primary solution with insights from alternatives.

        Primary:
        {json.dumps(primary, indent=2)[:800]}

        Alternatives:
        {alt_solutions}

        Return the merged solution in the same JSON structure as primary.
        """

        merged_text = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )

        try:
            merged = json.loads(merged_text)
            return merged
        except:
            logger.warning("Failed to merge alternatives, returning primary")
            return primary

    async def _update_learning(
        self,
        incident: Incident,
        response: EnhancedCAGResponse
    ):
        """Update learning components"""
        refinement_record = {
            "incident_category": incident.category,
            "incident_priority": incident.priority,
            "stages": response.total_stages,
            "improvement": response.improvement_percentage,
            "final_confidence": response.final_confidence,
            "consistency_score": response.consistency_score,
            "timestamp": datetime.now().isoformat()
        }

        self.refinement_history.append(refinement_record)

        # Update critic performance metrics
        for stage in response.stages:
            for evaluation in stage.critic_evaluations:
                self.critic_performance[evaluation.critic_name].append({
                    "score": evaluation.score,
                    "severity": evaluation.severity,
                    "processing_time": evaluation.processing_time
                })

        # Trim history
        max_history = 1000
        if len(self.refinement_history) > max_history:
            self.refinement_history = self.refinement_history[-max_history:]

        logger.info(f"Learning updated: {len(self.refinement_history)} refinements recorded")

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        if not self.refinement_history:
            return {"message": "No refinement history available"}

        avg_stages = np.mean([r['stages'] for r in self.refinement_history])
        avg_improvement = np.mean([r['improvement'] for r in self.refinement_history])
        avg_consistency = np.mean([r['consistency_score'] for r in self.refinement_history])

        critic_stats = {}
        for name, evals in self.critic_performance.items():
            if evals:
                critic_stats[name] = {
                    "total_evaluations": len(evals),
                    "average_score": np.mean([e['score'] for e in evals]),
                    "average_processing_time": np.mean([e['processing_time'] for e in evals]),
                    "severity_distribution": {
                        severity: sum(1 for e in evals if e['severity'] == severity)
                        for severity in ['low', 'medium', 'high', 'critical']
                    }
                }

        return {
            "total_refinements": len(self.refinement_history),
            "average_stages": avg_stages,
            "average_improvement": avg_improvement,
            "average_consistency_score": avg_consistency,
            "critic_statistics": critic_stats,
            "configuration": self.config
        }
