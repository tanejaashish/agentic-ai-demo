"""
Response validation utility for quality checks
"""

from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)

class ResponseValidator:
    """
    Validate and check quality of AI responses
    """
    
    def __init__(self):
        self.min_solution_steps = 2
        self.max_solution_steps = 10
        self.min_confidence = 0.3
        self.max_confidence = 1.0
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """
        Validate response and return list of issues
        """
        issues = []
        
        # Check if response has required fields
        if "recommendations" not in response:
            issues.append("Missing recommendations field")
            return issues
        
        recommendations = response.get("recommendations", [])
        
        if not recommendations:
            issues.append("No recommendations provided")
            return issues
        
        # Validate each recommendation
        for i, rec in enumerate(recommendations):
            rec_issues = self._validate_recommendation(rec, i)
            issues.extend(rec_issues)
        
        # Check confidence scores
        if "confidence" in response:
            conf = response["confidence"]
            if conf < self.min_confidence:
                issues.append(f"Confidence too low: {conf}")
            elif conf > self.max_confidence:
                issues.append(f"Invalid confidence: {conf}")
        
        return issues
    
    def _validate_recommendation(self, rec: Dict[str, Any], index: int) -> List[str]:
        """
        Validate individual recommendation
        """
        issues = []
        prefix = f"Recommendation {index + 1}"
        
        # Check solution steps
        if "solution_steps" not in rec:
            issues.append(f"{prefix}: Missing solution steps")
        else:
            steps = rec["solution_steps"]
            if not isinstance(steps, list):
                issues.append(f"{prefix}: Solution steps should be a list")
            elif len(steps) < self.min_solution_steps:
                issues.append(f"{prefix}: Too few solution steps ({len(steps)})")
            elif len(steps) > self.max_solution_steps:
                issues.append(f"{prefix}: Too many solution steps ({len(steps)})")
            else:
                # Check each step
                for j, step in enumerate(steps):
                    if not step or len(str(step).strip()) < 10:
                        issues.append(f"{prefix}: Step {j + 1} is too short or empty")
        
        # Check confidence
        if "confidence" in rec:
            conf = rec["confidence"]
            if not isinstance(conf, (int, float)):
                issues.append(f"{prefix}: Invalid confidence type")
            elif conf < 0 or conf > 1:
                issues.append(f"{prefix}: Confidence out of range: {conf}")
        
        return issues
    
    def check_completeness(self, response: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check if response is complete
        """
        completeness = {
            "has_recommendations": False,
            "has_root_cause": False,
            "has_prevention": False,
            "has_confidence": False,
            "has_sources": False,
            "is_actionable": False
        }
        
        if "recommendations" in response and response["recommendations"]:
            completeness["has_recommendations"] = True
            
            # Check first recommendation for details
            first_rec = response["recommendations"][0]
            
            if "root_cause" in first_rec and first_rec["root_cause"]:
                completeness["has_root_cause"] = True
            
            if "prevention" in first_rec and first_rec["prevention"]:
                completeness["has_prevention"] = True
            
            if "solution_steps" in first_rec and first_rec["solution_steps"]:
                completeness["is_actionable"] = True
        
        if "confidence" in response:
            completeness["has_confidence"] = True
        
        if "sources" in response or "rag_sources" in response:
            completeness["has_sources"] = True
        
        return completeness
    
    def check_clarity(self, text: str) -> Dict[str, Any]:
        """
        Check text clarity metrics
        """
        if not text:
            return {"score": 0, "issues": ["Empty text"]}
        
        issues = []
        score = 1.0
        
        # Check for technical jargon overload
        jargon_count = len(re.findall(r'\b[A-Z]{3,}\b', text))
        if jargon_count > 5:
            issues.append("Too much technical jargon")
            score -= 0.2
        
        # Check sentence length
        sentences = re.split(r'[.!?]+', text)
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        if long_sentences:
            issues.append(f"{len(long_sentences)} sentences are too long")
            score -= 0.1 * len(long_sentences)
        
        # Check for vague terms
        vague_terms = ['somehow', 'something', 'stuff', 'things', 'maybe', 'possibly']
        vague_count = sum(1 for term in vague_terms if term in text.lower())
        if vague_count > 2:
            issues.append("Contains vague terminology")
            score -= 0.15
        
        # Check for actionable language
        action_words = ['check', 'verify', 'update', 'restart', 'configure', 'review']
        has_actions = any(word in text.lower() for word in action_words)
        if not has_actions:
            issues.append("Lacks actionable language")
            score -= 0.2
        
        return {
            "score": max(0, score),
            "issues": issues,
            "is_clear": score > 0.7
        }
    
    def check_consistency(self, response: Dict[str, Any]) -> List[str]:
        """
        Check for internal consistency in response
        """
        inconsistencies = []
        
        recommendations = response.get("recommendations", [])
        
        if len(recommendations) > 1:
            # Check if recommendations contradict each other
            all_steps = []
            for rec in recommendations:
                if "solution_steps" in rec:
                    all_steps.extend(rec["solution_steps"])
            
            # Simple contradiction detection
            if any("restart" in step.lower() for step in all_steps) and \
               any("do not restart" in step.lower() for step in all_steps):
                inconsistencies.append("Contradictory restart instructions")
            
            # Check confidence consistency
            confidences = [rec.get("confidence", 0) for rec in recommendations]
            if confidences:
                conf_range = max(confidences) - min(confidences)
                if conf_range > 0.5:
                    inconsistencies.append("Large variance in confidence scores")
        
        return inconsistencies