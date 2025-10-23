"""
CAG (Corrective Augmented Generation) Agent
Refines and corrects RAG responses through iterative improvement
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np
import logging

from app.services.llm_service import LLMService
#from app.agents.rag_agent import RAGAgent, RAGResponse
from app.models.incident import Incident
from app.utils.validation import ResponseValidator

from app.agents.rag_agent import LangChainRAGAgent as RAGAgent

# Define RAGResponse here if not in rag_agent
class RAGResponse:
    def __init__(self, recommendations=None, confidence=0.5, sources=None):
        self.recommendations = recommendations or []
        self.confidence = confidence
        self.sources = sources or []

logger = logging.getLogger(__name__)

@dataclass
class CAGIteration:
    """Single iteration of CAG refinement"""
    iteration_number: int
    input_response: Dict[str, Any]
    corrections: List[Dict[str, Any]]
    refined_response: Dict[str, Any]
    confidence_before: float
    confidence_after: float
    issues_found: List[str]
    improvements: List[str]

@dataclass
class CAGResponse:
    """Complete CAG refinement response"""
    final_recommendations: List[Dict[str, Any]]
    final_confidence: float
    iterations: List[CAGIteration]
    total_iterations: int
    improvement_percentage: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class CAGAgent:
    """
    Corrective Augmented Generation Agent
    Identifies and corrects issues in RAG responses through:
    - Self-reflection and critique
    - Fact verification
    - Consistency checking
    - Iterative refinement
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_agent: Optional[RAGAgent] = None,
        config: Optional[Dict] = None
    ):
        self.llm_service = llm_service
        self.rag_agent = rag_agent
        self.validator = ResponseValidator()
        
        # Configuration
        self.config = config or {}
        self.max_iterations = self.config.get('max_iterations', 3)
        self.confidence_target = self.config.get('confidence_target', 0.85)
        self.correction_threshold = self.config.get('correction_threshold', 0.7)
        self.feedback_weight = self.config.get('feedback_weight', 0.3)
        self.enable_fact_checking = self.config.get('enable_fact_checking', True)
        self.enable_consistency_check = self.config.get('enable_consistency_check', True)
        
        # Learning components
        self.correction_history = []
        self.success_patterns = []
        self.failure_patterns = []
        
        logger.info("CAG Agent initialized with configuration: %s", self.config)
    
    async def refine(
        self,
        incident: Incident,
        rag_response: RAGResponse,
        max_iterations: Optional[int] = None
    ) -> CAGResponse:
        """
        Main refinement method - iteratively improves RAG response
        """
        start_time = datetime.now()
        iterations = []
        current_response = self._convert_rag_to_dict(rag_response)
        current_confidence = rag_response.confidence
        initial_confidence = current_confidence
        
        max_iter = max_iterations or self.max_iterations
        
        for iteration in range(max_iter):
            logger.info(f"CAG Iteration {iteration + 1}/{max_iter}, Current confidence: {current_confidence:.2f}")
            
            # Check if we've reached target confidence
            if current_confidence >= self.confidence_target:
                logger.info(f"Target confidence {self.confidence_target} reached")
                break
            
            # Perform one iteration of refinement
            iteration_result = await self._refine_iteration(
                incident=incident,
                current_response=current_response,
                current_confidence=current_confidence,
                iteration_number=iteration + 1
            )
            
            iterations.append(iteration_result)
            
            # Update current state
            current_response = iteration_result.refined_response
            current_confidence = iteration_result.confidence_after
            
            # Check for convergence (no significant improvement)
            if abs(iteration_result.confidence_after - iteration_result.confidence_before) < 0.01:
                logger.info("Convergence reached - no significant improvement")
                break
        
        # Calculate improvement metrics
        improvement = ((current_confidence - initial_confidence) / initial_confidence) * 100 if initial_confidence > 0 else 0
        
        # Prepare final response
        response = CAGResponse(
            final_recommendations=current_response.get('recommendations', []),
            final_confidence=current_confidence,
            iterations=iterations,
            total_iterations=len(iterations),
            improvement_percentage=improvement,
            sources=rag_response.sources,
            metadata={
                "initial_confidence": initial_confidence,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "converged": current_confidence >= self.confidence_target,
                "cag_config": self.config
            }
        )
        
        # Learn from this refinement
        await self._update_learning(incident, response)
        
        logger.info(f"CAG refinement completed: {len(iterations)} iterations, {improvement:.1f}% improvement")
        return response
    
    async def _refine_iteration(
        self,
        incident: Incident,
        current_response: Dict[str, Any],
        current_confidence: float,
        iteration_number: int
    ) -> CAGIteration:
        """
        Perform one iteration of refinement
        """
        # Step 1: Identify issues in current response
        issues = await self._identify_issues(incident, current_response)
        
        # Step 2: Generate corrections for identified issues
        corrections = await self._generate_corrections(incident, current_response, issues)
        
        # Step 3: Apply corrections to create refined response
        refined_response = await self._apply_corrections(current_response, corrections)
        
        # Step 4: Validate refined response
        if self.enable_consistency_check:
            refined_response = await self._ensure_consistency(incident, refined_response)
        
        # Step 5: Calculate new confidence
        new_confidence = await self._calculate_refined_confidence(
            incident, refined_response, issues, corrections
        )
        
        # Step 6: Identify improvements made
        improvements = self._identify_improvements(current_response, refined_response)
        
        return CAGIteration(
            iteration_number=iteration_number,
            input_response=current_response,
            corrections=corrections,
            refined_response=refined_response,
            confidence_before=current_confidence,
            confidence_after=new_confidence,
            issues_found=issues,
            improvements=improvements
        )
    
    async def _identify_issues(
        self,
        incident: Incident,
        response: Dict[str, Any]
    ) -> List[str]:
        """
        Identify issues in the current response using self-reflection
        """
        issues = []
        
        # Use LLM for self-critique
        critique_prompt = f"""
        Analyze the following incident response and identify any issues, weaknesses, or areas for improvement.
        
        Incident:
        Title: {incident.title}
        Description: {incident.description}
        Priority: {incident.priority}
        
        Current Response:
        {json.dumps(response, indent=2)}
        
        Check for:
        1. Completeness - Are all aspects of the incident addressed?
        2. Accuracy - Are the technical details correct?
        3. Clarity - Are the instructions clear and actionable?
        4. Relevance - Does the solution match the problem?
        5. Feasibility - Can the solution be implemented with available resources?
        6. Risk - Are there any potential risks not addressed?
        
        List specific issues found (one per line):
        """
        
        critique_response = await self.llm_service.generate(
            prompt=critique_prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        # Parse issues from response
        issues.extend([
            issue.strip() 
            for issue in critique_response.split('\n') 
            if issue.strip() and not issue.startswith('#')
        ])
        
        # Additional validation checks
        validation_issues = self.validator.validate_response(response)
        issues.extend(validation_issues)
        
        # Fact checking if enabled
        if self.enable_fact_checking:
            fact_issues = await self._check_facts(incident, response)
            issues.extend(fact_issues)
        
        logger.info(f"Identified {len(issues)} issues in current response")
        return issues[:10]  # Limit to top 10 issues to prevent over-correction
    
    async def _generate_corrections(
        self,
        incident: Incident,
        response: Dict[str, Any],
        issues: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific corrections for identified issues
        """
        corrections = []
        
        if not issues:
            return corrections
        
        # Generate corrections for each issue
        correction_prompt = f"""
        Generate specific corrections for the following issues in the incident response.
        
        Incident Context:
        {incident.title}: {incident.description}
        
        Current Response Summary:
        {json.dumps(response.get('recommendations', [{}])[0], indent=2)[:500]}
        
        Issues to Address:
        {chr(10).join(f"{i+1}. {issue}" for i, issue in enumerate(issues))}
        
        For each issue, provide a specific correction in JSON format:
        {{
            "issue_number": <number>,
            "correction_type": "addition|modification|removal|clarification",
            "target_field": "field_to_modify",
            "correction_content": "specific correction text or data",
            "rationale": "why this correction improves the response"
        }}
        
        Provide corrections as a JSON array:
        """
        
        correction_response = await self.llm_service.generate(
            prompt=correction_prompt,
            max_tokens=800,
            temperature=0.2
        )
        
        try:
            # Parse JSON response
            corrections = json.loads(correction_response)
            if not isinstance(corrections, list):
                corrections = [corrections]
                
        except json.JSONDecodeError:
            # Fallback: create generic corrections
            for i, issue in enumerate(issues[:5]):
                corrections.append({
                    "issue_number": i + 1,
                    "correction_type": "modification",
                    "target_field": "solution_steps",
                    "correction_content": f"Address: {issue}",
                    "rationale": "Improve response quality"
                })
        
        logger.info(f"Generated {len(corrections)} corrections")
        return corrections
    
    async def _apply_corrections(
        self,
        response: Dict[str, Any],
        corrections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply corrections to create refined response
        """
        refined = json.loads(json.dumps(response))  # Deep copy
        
        for correction in corrections:
            try:
                corr_type = correction.get('correction_type', 'modification')
                target = correction.get('target_field', '')
                content = correction.get('correction_content', '')
                
                if corr_type == 'addition':
                    # Add new content
                    if target in refined:
                        if isinstance(refined[target], list):
                            refined[target].append(content)
                        else:
                            refined[target] = f"{refined[target]} {content}"
                    else:
                        refined[target] = content
                        
                elif corr_type == 'modification':
                    # Modify existing content
                    refined[target] = content
                    
                elif corr_type == 'removal':
                    # Remove content
                    if target in refined:
                        del refined[target]
                        
                elif corr_type == 'clarification':
                    # Clarify existing content
                    if target in refined:
                        refined[target] = f"{refined[target]} (Clarification: {content})"
                        
            except Exception as e:
                logger.warning(f"Failed to apply correction: {e}")
                continue
        
        # Ensure recommendations structure is maintained
        if 'recommendations' not in refined:
            refined['recommendations'] = response.get('recommendations', [])
        
        return refined
    
    async def _ensure_consistency(
        self,
        incident: Incident,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ensure internal consistency of the response
        """
        consistency_prompt = f"""
        Review this incident response for internal consistency.
        Fix any contradictions or inconsistencies.
        
        Incident: {incident.title}
        
        Response to review:
        {json.dumps(response, indent=2)}
        
        Return the response with any consistency issues fixed.
        Maintain the same JSON structure.
        """
        
        consistent_response = await self.llm_service.generate(
            prompt=consistency_prompt,
            max_tokens=1000,
            temperature=0.1
        )
        
        try:
            return json.loads(consistent_response)
        except:
            return response  # Return original if parsing fails
    
    async def _check_facts(
        self,
        incident: Incident,
        response: Dict[str, Any]
    ) -> List[str]:
        """
        Verify factual accuracy of the response
        """
        issues = []
        
        # Check for common factual errors in IT support
        fact_check_prompt = f"""
        Check the technical accuracy of this response.
        Identify any factual errors or misleading information.
        
        Response: {json.dumps(response.get('recommendations', [{}])[0], indent=2)[:500]}
        
        List any factual errors (one per line):
        """
        
        fact_errors = await self.llm_service.generate(
            prompt=fact_check_prompt,
            max_tokens=300,
            temperature=0.2
        )
        
        issues.extend([
            f"Factual error: {error.strip()}"
            for error in fact_errors.split('\n')
            if error.strip()
        ])
        
        return issues
    
    async def _calculate_refined_confidence(
        self,
        incident: Incident,
        refined_response: Dict[str, Any],
        issues: List[str],
        corrections: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for refined response
        """
        # Base confidence from number of issues resolved
        issues_resolved_ratio = len(corrections) / max(len(issues), 1)
        
        # Get quality assessment from LLM
        quality_prompt = f"""
        Rate the quality of this incident response on a scale of 0-100.
        Consider completeness, accuracy, clarity, and actionability.
        
        Response: {json.dumps(refined_response.get('recommendations', [{}])[0], indent=2)[:500]}
        
        Return only the numeric score:
        """
        
        quality_score = await self.llm_service.generate(
            prompt=quality_prompt,
            max_tokens=10,
            temperature=0.1
        )
        
        try:
            quality_rating = float(quality_score.strip()) / 100
        except:
            quality_rating = 0.7  # Default fallback
        
        # Combine factors
        confidence = (
            0.3 * issues_resolved_ratio +
            0.5 * quality_rating +
            0.2 * min(len(corrections) / 3, 1.0)  # Bonus for corrections applied
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def _identify_improvements(
        self,
        original: Dict[str, Any],
        refined: Dict[str, Any]
    ) -> List[str]:
        """
        Identify specific improvements made
        """
        improvements = []
        
        # Check for added content
        for key in refined:
            if key not in original:
                improvements.append(f"Added {key}")
            elif refined[key] != original.get(key):
                improvements.append(f"Improved {key}")
        
        # Check for structural improvements
        if 'recommendations' in refined:
            orig_recs = len(original.get('recommendations', []))
            new_recs = len(refined.get('recommendations', []))
            if new_recs > orig_recs:
                improvements.append(f"Added {new_recs - orig_recs} recommendations")
        
        return improvements
    
    def _convert_rag_to_dict(self, rag_response: RAGResponse) -> Dict[str, Any]:
        """
        Convert RAG response to dictionary format for processing
        """
        return {
            "recommendations": rag_response.recommendations,
            "confidence": rag_response.confidence,
            "sources": rag_response.sources,
            "metadata": rag_response.metadata
        }
    
    async def _update_learning(self, incident: Incident, response: CAGResponse):
        """
        Update learning components based on refinement results
        """
        # Record correction patterns
        correction_pattern = {
            "incident_type": incident.category,
            "iterations": response.total_iterations,
            "improvement": response.improvement_percentage,
            "final_confidence": response.final_confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        self.correction_history.append(correction_pattern)
        
        # Identify success/failure patterns
        if response.final_confidence >= self.confidence_target:
            self.success_patterns.append({
                "pattern": self._extract_pattern(incident),
                "iterations": response.total_iterations
            })
        else:
            self.failure_patterns.append({
                "pattern": self._extract_pattern(incident),
                "issues": sum(len(it.issues_found) for it in response.iterations)
            })
        
        # Trim history to prevent memory growth
        max_history = 1000
        if len(self.correction_history) > max_history:
            self.correction_history = self.correction_history[-max_history:]
        
        logger.info(f"Learning updated: {len(self.correction_history)} patterns recorded")
    
    def _extract_pattern(self, incident: Incident) -> Dict[str, Any]:
        """
        Extract pattern from incident for learning
        """
        return {
            "category": incident.category,
            "priority": incident.priority,
            "has_error": bool(incident.error_message),
            "systems_count": len(incident.affected_systems) if incident.affected_systems else 0
        }
    
    async def get_correction_stats(self) -> Dict[str, Any]:
        """
        Get statistics about CAG corrections
        """
        if not self.correction_history:
            return {"message": "No correction history available"}
        
        avg_iterations = np.mean([h['iterations'] for h in self.correction_history])
        avg_improvement = np.mean([h['improvement'] for h in self.correction_history])
        success_rate = len(self.success_patterns) / max(len(self.correction_history), 1)
        
        return {
            "total_corrections": len(self.correction_history),
            "average_iterations": avg_iterations,
            "average_improvement": avg_improvement,
            "success_rate": success_rate,
            "success_patterns": len(self.success_patterns),
            "failure_patterns": len(self.failure_patterns)
        }