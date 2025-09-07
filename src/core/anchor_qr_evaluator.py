"""
ANCHOR-QR-8 Evaluation Protocol for PromptCraft CREATE Framework.

This module implements the ANCHOR-QR-8 evaluation protocol, a comprehensive 6-step
quality assurance system for validating CREATE framework prompts. The protocol ensures
professional-grade prompt quality through systematic evaluation and diagnostic flagging.

The ANCHOR-QR protocol provides:
- E.1: Reflection Loop with iterative revision capabilities
- E.2: Self-Consistency Check with multiple reasoning paths
- E.3: Chain-of-Verification (CoVe) for complex claims validation
- E.4: Confidence, Sourcing and Accuracy assessment with diagnostic flags
- E.5: Style, Safety and Constraint Pass for compliance verification
- E.6: Overall Fitness and Final Review for holistic quality assessment

Architecture:
    The evaluator processes CREATE framework prompts through six sequential steps,
    each building upon the previous to provide comprehensive quality validation.
    Results include numeric scores, diagnostic flags, and actionable recommendations.

Key Components:
    - Systematic 6-step evaluation methodology
    - Diagnostic flag generation for quality issues
    - Confidence scoring and uncertainty quantification
    - Rigor level adaptation (Basic/Intermediate/Advanced)
    - Professional quality standards enforcement

Dependencies:
    - src.utils.logging_mixin: For structured logging and error handling
    - dataclasses: For evaluation result data structures
    - enum: For standardized evaluation categories and flags

Called by:
    - src.agents.create_agent: For prompt quality validation
    - src.ui.journeys.journey1_smart_templates: For evaluation integration
    - Quality assurance systems: For systematic prompt review

Complexity: O(n*m) where n is prompt length and m is evaluation depth
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.utils.logging_mixin import LoggerMixin

# Constants for ANCHOR-QR-8 evaluation thresholds
HIGH_CONFIDENCE_THRESHOLD = 85
MEDIUM_CONFIDENCE_THRESHOLD = 60
LOW_CONFIDENCE_THRESHOLD = 40
MINIMUM_WORD_COUNT_COMPLEX = 100
EXPERT_JUDGMENT_KEYWORDS = [
    "best practice", "recommended approach", "industry standard", "expert opinion",
    "professional judgment", "proven method", "established practice"
]

# Stylometry thresholds per ANCHOR-QR-7 standards
MIN_HEDGE_DENSITY = 5  # Percentage
MAX_HEDGE_DENSITY = 10  # Percentage
MIN_LEXICAL_DIVERSITY = 0.40  # TTR threshold
MIN_SENTENCE_VARIABILITY = 15  # Percentage short/long sentences
AVERAGE_SENTENCE_LENGTH_TARGET = (17, 22)  # Word range


class RigorLevel(str, Enum):
    """Evaluation rigor levels for ANCHOR-QR-8 protocol."""
    
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"


class DiagnosticFlag(str, Enum):
    """Diagnostic flags for prompt quality issues."""
    
    EXPERT_JUDGMENT = "ExpertJudgment"
    CONFIDENCE_LOW = "Confidence:Low"
    CONFIDENCE_MEDIUM = "Confidence:Medium"
    CONFIDENCE_HIGH = "Confidence:High"
    VERIFICATION_ISSUE = "VerificationIssue"
    DATA_UNAVAILABLE = "DataUnavailableOrUnverified"
    STYLE_VIOLATION = "StyleViolation"
    SAFETY_CONCERN = "SafetyConcern"


class EvaluationStep(str, Enum):
    """ANCHOR-QR-8 evaluation steps."""
    
    REFLECTION_LOOP = "reflection_loop"
    SELF_CONSISTENCY = "self_consistency_check"
    CHAIN_OF_VERIFICATION = "chain_of_verification"
    CONFIDENCE_SOURCING = "confidence_sourcing_accuracy"
    STYLE_SAFETY = "style_safety_constraint_pass"
    OVERALL_FITNESS = "overall_fitness_final_review"


@dataclass
class EvaluationResult:
    """Results from a single ANCHOR-QR-8 evaluation step."""
    
    step: EvaluationStep
    score: float  # 0-100 quality score
    confidence: float  # 0-100 confidence in evaluation
    flags: List[DiagnosticFlag] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComprehensiveEvaluation:
    """Complete ANCHOR-QR-8 evaluation results."""
    
    overall_score: float  # Weighted average across all steps
    overall_confidence: float  # Confidence in the evaluation
    rigor_level: RigorLevel
    step_results: Dict[EvaluationStep, EvaluationResult] = field(default_factory=dict)
    all_flags: Set[DiagnosticFlag] = field(default_factory=set)
    critical_issues: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0  # CREATE framework compliance (0-100)
    
    @property
    def is_passing(self) -> bool:
        """Determine if evaluation passes quality threshold (>70 overall score)."""
        return self.overall_score >= 70.0
    
    @property
    def needs_revision(self) -> bool:
        """Determine if prompt needs significant revision."""
        return (
            self.overall_score < 50.0 or 
            len(self.critical_issues) > 0 or
            DiagnosticFlag.SAFETY_CONCERN in self.all_flags
        )


class ANCHORQREvaluator(LoggerMixin):
    """
    ANCHOR-QR-8 evaluation protocol implementation for CREATE framework prompts.
    
    This evaluator systematically assesses prompt quality through six evaluation steps,
    generating diagnostic flags, confidence scores, and actionable recommendations
    for improvement.
    
    Features:
    - Complete 6-step ANCHOR-QR-8 protocol implementation
    - Adaptive rigor levels based on prompt complexity
    - Diagnostic flag generation for common quality issues
    - Stylometry validation per ANCHOR-QR-7 standards
    - Confidence scoring and uncertainty quantification
    """
    
    def __init__(self) -> None:
        """Initialize the ANCHOR-QR evaluator with default settings."""
        super().__init__()
        self.evaluation_weights = {
            EvaluationStep.REFLECTION_LOOP: 0.15,
            EvaluationStep.SELF_CONSISTENCY: 0.20,
            EvaluationStep.CHAIN_OF_VERIFICATION: 0.20,
            EvaluationStep.CONFIDENCE_SOURCING: 0.20,
            EvaluationStep.STYLE_SAFETY: 0.15,
            EvaluationStep.OVERALL_FITNESS: 0.10
        }
    
    def evaluate_prompt(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel = RigorLevel.STANDARD
    ) -> ComprehensiveEvaluation:
        """
        Execute complete ANCHOR-QR-8 evaluation protocol on a CREATE framework prompt.
        
        Args:
            prompt: The CREATE framework prompt to evaluate
            context: Context information including query, analysis, preferences
            rigor_level: Evaluation rigor level (Basic/Standard/Advanced)
            
        Returns:
            Comprehensive evaluation results with scores, flags, and recommendations
            
        Time Complexity: O(n*k) where n is prompt length and k is rigor level factor
        Space Complexity: O(n) for evaluation data structures
        """
        try:
            self.logger.info(f"Starting ANCHOR-QR-8 evaluation with {rigor_level.value} rigor")
            
            # Initialize evaluation
            evaluation = ComprehensiveEvaluation(
                overall_score=0.0,
                overall_confidence=0.0,
                rigor_level=rigor_level
            )
            
            # Execute all evaluation steps
            for step in EvaluationStep:
                step_result = self._evaluate_step(step, prompt, context, rigor_level)
                evaluation.step_results[step] = step_result
                evaluation.all_flags.update(step_result.flags)
            
            # Calculate overall scores
            evaluation.overall_score = self._calculate_weighted_score(evaluation.step_results)
            evaluation.overall_confidence = self._calculate_overall_confidence(evaluation.step_results)
            evaluation.compliance_score = self._calculate_create_compliance(prompt, evaluation.step_results)
            
            # Identify critical issues
            evaluation.critical_issues = self._identify_critical_issues(evaluation)
            evaluation.improvement_recommendations = self._generate_improvement_recommendations(evaluation)
            
            self.logger.info(
                f"ANCHOR-QR-8 evaluation complete. "
                f"Score: {evaluation.overall_score:.1f}, "
                f"Flags: {len(evaluation.all_flags)}, "
                f"Issues: {len(evaluation.critical_issues)}"
            )
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"ANCHOR-QR-8 evaluation failed: {e}")
            return self._create_error_evaluation(str(e), rigor_level)
    
    def _evaluate_step(
        self,
        step: EvaluationStep,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """Execute a single ANCHOR-QR-8 evaluation step."""
        evaluation_method = getattr(self, f"_evaluate_{step.value}")
        return evaluation_method(prompt, context, rigor_level)
    
    def _evaluate_reflection_loop(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.1: Reflection Loop - Self-critique and iterative revision assessment."""
        result = EvaluationResult(
            step=EvaluationStep.REFLECTION_LOOP,
            score=75.0,  # Base score
            confidence=80.0
        )
        
        # Check if prompt addresses original query comprehensively
        original_query = context.get("query", "")
        if not original_query.strip():
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append("Original query not available for reflection assessment")
            result.score -= 20
        
        # Analyze prompt structure completeness
        create_components = ["# C - Context", "# R - Request", "# E - Examples", 
                           "# A - Augmentations", "# T - Tone", "# E - Evaluation"]
        missing_components = [comp for comp in create_components if comp not in prompt]
        
        if missing_components:
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append(f"Missing CREATE components: {', '.join(missing_components)}")
            result.score -= len(missing_components) * 10
        
        # Check for self-reflection elements
        reflection_indicators = [
            "does the response", "ensure that", "verify", "confirm", "check"
        ]
        reflection_count = sum(1 for indicator in reflection_indicators if indicator in prompt.lower())
        
        if reflection_count < 2:
            result.recommendations.append("Add more self-reflection prompts to encourage iterative thinking")
            result.score -= 5
        
        result.metadata["missing_components"] = missing_components
        result.metadata["reflection_indicators"] = reflection_count
        
        return result
    
    def _evaluate_self_consistency_check(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.2: Self-Consistency Check - Multiple reasoning paths validation."""
        result = EvaluationResult(
            step=EvaluationStep.SELF_CONSISTENCY,
            score=70.0,
            confidence=75.0
        )
        
        # Check for multiple reasoning approaches
        reasoning_keywords = [
            "step by step", "alternative", "consider", "approach", "method", 
            "perspective", "viewpoint", "reasoning path"
        ]
        reasoning_count = sum(1 for keyword in reasoning_keywords if keyword in prompt.lower())
        
        if reasoning_count >= 3:
            result.score += 10
        elif reasoning_count < 2:
            result.recommendations.append("Include multiple reasoning approaches or perspectives")
            result.score -= 10
        
        # Check for consistency requirements
        consistency_indicators = [
            "consistent", "coherent", "logical", "contradictory", "align"
        ]
        consistency_count = sum(1 for indicator in consistency_indicators if indicator in prompt.lower())
        
        if consistency_count == 0:
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append("No consistency checking requirements specified")
            result.score -= 15
        
        # Advanced rigor: Check for comparative analysis requirements
        if rigor_level == RigorLevel.ADVANCED:
            comparative_elements = ["compare", "contrast", "evaluate alternatives", "weigh options"]
            comparative_count = sum(1 for elem in comparative_elements if elem in prompt.lower())
            
            if comparative_count == 0:
                result.recommendations.append("Add comparative analysis requirements for advanced rigor")
                result.score -= 5
        
        result.metadata["reasoning_count"] = reasoning_count
        result.metadata["consistency_count"] = consistency_count
        
        return result
    
    def _evaluate_chain_of_verification(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.3: Chain-of-Verification - Complex claims validation assessment."""
        result = EvaluationResult(
            step=EvaluationStep.CHAIN_OF_VERIFICATION,
            score=65.0,
            confidence=70.0
        )
        
        # Check for verification requirements
        verification_keywords = [
            "verify", "validate", "confirm", "check", "ensure accuracy", 
            "fact-check", "cross-reference", "substantiate"
        ]
        verification_count = sum(1 for keyword in verification_keywords if keyword in prompt.lower())
        
        if verification_count >= 2:
            result.score += 15
        elif verification_count == 0:
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append("No verification requirements specified for complex claims")
            result.score -= 20
        
        # Check for evidence requirements
        evidence_keywords = [
            "evidence", "source", "citation", "reference", "documentation",
            "support", "substantiate", "back up"
        ]
        evidence_count = sum(1 for keyword in evidence_keywords if keyword in prompt.lower())
        
        if evidence_count == 0:
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append("No evidence requirements specified")
            result.score -= 15
        
        # Check for uncertainty handling
        uncertainty_keywords = [
            "uncertain", "unclear", "unknown", "cannot determine", 
            "insufficient information", "hedge", "qualifying"
        ]
        uncertainty_count = sum(1 for keyword in uncertainty_keywords if keyword in prompt.lower())
        
        if uncertainty_count == 0:
            result.recommendations.append("Add requirements for handling uncertain or incomplete information")
            result.score -= 5
        
        result.metadata["verification_count"] = verification_count
        result.metadata["evidence_count"] = evidence_count
        result.metadata["uncertainty_count"] = uncertainty_count
        
        return result
    
    def _evaluate_confidence_sourcing_accuracy(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.4: Confidence, Sourcing and Accuracy - Source attribution assessment."""
        result = EvaluationResult(
            step=EvaluationStep.CONFIDENCE_SOURCING,
            score=70.0,
            confidence=85.0
        )
        
        # Check for expert judgment indicators
        expert_judgment_count = sum(
            1 for keyword in EXPERT_JUDGMENT_KEYWORDS 
            if keyword in prompt.lower()
        )
        
        if expert_judgment_count > 0:
            result.flags.append(DiagnosticFlag.EXPERT_JUDGMENT)
            result.metadata["expert_judgment_areas"] = expert_judgment_count
        
        # Check for sourcing requirements
        sourcing_requirements = [
            "cite", "reference", "source", "attribution", "documentation"
        ]
        sourcing_count = sum(1 for req in sourcing_requirements if req in prompt.lower())
        
        if sourcing_count >= 2:
            result.score += 10
        elif sourcing_count == 0:
            result.issues.append("No sourcing requirements specified")
            result.score -= 15
        
        # Check for confidence indicators
        confidence_requirements = [
            "confidence", "certainty", "reliability", "accuracy", "precision"
        ]
        confidence_count = sum(1 for req in confidence_requirements if req in prompt.lower())
        
        if confidence_count == 0:
            result.recommendations.append("Add confidence assessment requirements")
            result.score -= 5
        
        # Advanced rigor: Check for quantitative accuracy requirements
        if rigor_level == RigorLevel.ADVANCED:
            quantitative_keywords = [
                "measurable", "specific", "quantifiable", "numerical", "percentage"
            ]
            quantitative_count = sum(1 for keyword in quantitative_keywords if keyword in prompt.lower())
            
            if quantitative_count == 0:
                result.recommendations.append("Add quantitative accuracy requirements for advanced rigor")
        
        result.metadata["sourcing_count"] = sourcing_count
        result.metadata["confidence_count"] = confidence_count
        
        return result
    
    def _evaluate_style_safety_constraint_pass(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.5: Style, Safety and Constraint Pass - Compliance verification."""
        result = EvaluationResult(
            step=EvaluationStep.STYLE_SAFETY,
            score=75.0,
            confidence=90.0
        )
        
        # Check for stylometry requirements
        stylometry_score = self._evaluate_stylometry_requirements(prompt)
        result.score = (result.score + stylometry_score) / 2
        
        # Check for safety considerations
        safety_keywords = [
            "safety", "security", "privacy", "bias", "harmful", "ethical"
        ]
        safety_count = sum(1 for keyword in safety_keywords if keyword in prompt.lower())
        
        if context.get("query_analysis", {}).get("complexity") == "complex" and safety_count == 0:
            result.flags.append(DiagnosticFlag.SAFETY_CONCERN)
            result.issues.append("Complex query lacks safety consideration requirements")
            result.score -= 10
        
        # Check for constraint specifications
        constraint_keywords = [
            "constraint", "limitation", "boundary", "scope", "restriction"
        ]
        constraint_count = sum(1 for keyword in constraint_keywords if keyword in prompt.lower())
        
        if constraint_count == 0:
            result.recommendations.append("Add clear constraint specifications")
            result.score -= 5
        
        # Check for prohibited AI references (CREATE framework rule)
        ai_references = [
            "ai", "artificial intelligence", "language model", "chatbot", "assistant"
        ]
        ai_reference_count = sum(1 for ref in ai_references if ref in prompt.lower())
        
        if ai_reference_count > 1:  # Allow minimal references in instructions
            result.flags.append(DiagnosticFlag.STYLE_VIOLATION)
            result.issues.append("Excessive AI/LLM references in role definitions")
            result.score -= 10
        
        result.metadata["safety_count"] = safety_count
        result.metadata["constraint_count"] = constraint_count
        result.metadata["ai_references"] = ai_reference_count
        
        return result
    
    def _evaluate_overall_fitness_final_review(
        self,
        prompt: str,
        context: Dict[str, Any],
        rigor_level: RigorLevel
    ) -> EvaluationResult:
        """E.6: Overall Fitness and Final Review - Holistic quality assessment."""
        result = EvaluationResult(
            step=EvaluationStep.OVERALL_FITNESS,
            score=80.0,
            confidence=85.0
        )
        
        # Assess prompt completeness
        word_count = len(prompt.split())
        expected_min_words = {
            RigorLevel.BASIC: 200,
            RigorLevel.STANDARD: 400,
            RigorLevel.ADVANCED: 600
        }
        
        min_words = expected_min_words[rigor_level]
        if word_count < min_words:
            result.flags.append(DiagnosticFlag.VERIFICATION_ISSUE)
            result.issues.append(f"Prompt too short for {rigor_level.value} rigor ({word_count}/{min_words} words)")
            result.score -= 15
        
        # Check for actionability
        actionable_keywords = [
            "actionable", "specific", "implement", "apply", "use", "execute"
        ]
        actionable_count = sum(1 for keyword in actionable_keywords if keyword in prompt.lower())
        
        if actionable_count < 2:
            result.recommendations.append("Increase actionability requirements for practical value")
            result.score -= 5
        
        # Assess professional quality indicators
        professional_keywords = [
            "professional", "business", "industry", "standard", "best practice"
        ]
        professional_count = sum(1 for keyword in professional_keywords if keyword in prompt.lower())
        
        if professional_count >= 2:
            result.score += 5
        
        # Check for clear success criteria
        success_indicators = [
            "success criteria", "quality standard", "evaluation", "assessment"
        ]
        success_count = sum(1 for indicator in success_indicators if indicator in prompt.lower())
        
        if success_count == 0:
            result.issues.append("No clear success criteria specified")
            result.score -= 10
        
        result.metadata["word_count"] = word_count
        result.metadata["actionable_count"] = actionable_count
        result.metadata["professional_count"] = professional_count
        result.metadata["success_count"] = success_count
        
        return result
    
    def _evaluate_stylometry_requirements(self, prompt: str) -> float:
        """Evaluate adherence to ANCHOR-QR-7 stylometry standards."""
        score = 70.0  # Base score
        
        # Check for hedge density requirements
        hedge_words = ["may", "might", "could", "possibly", "likely", "potentially", "suggest"]
        sentences = re.split(r'[.!?]+', prompt)
        hedge_sentences = sum(1 for sentence in sentences if any(hedge in sentence.lower() for hedge in hedge_words))
        
        if len(sentences) > 0:
            hedge_density = (hedge_sentences / len(sentences)) * 100
            if MIN_HEDGE_DENSITY <= hedge_density <= MAX_HEDGE_DENSITY:
                score += 10
            elif hedge_density < MIN_HEDGE_DENSITY:
                score -= 5
        
        # Check for lexical diversity indicators
        diversity_keywords = [
            "varied", "diverse", "different", "alternative", "various"
        ]
        diversity_count = sum(1 for keyword in diversity_keywords if keyword in prompt.lower())
        
        if diversity_count >= 2:
            score += 5
        
        # Check for sentence variability requirements
        variability_keywords = [
            "variability", "mix", "range", "different lengths", "short and long"
        ]
        variability_count = sum(1 for keyword in variability_keywords if keyword in prompt.lower())
        
        if variability_count > 0:
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_weighted_score(self, step_results: Dict[EvaluationStep, EvaluationResult]) -> float:
        """Calculate weighted overall score from step results."""
        total_score = 0.0
        total_weight = 0.0
        
        for step, result in step_results.items():
            weight = self.evaluation_weights.get(step, 0.1)
            total_score += result.score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_overall_confidence(self, step_results: Dict[EvaluationStep, EvaluationResult]) -> float:
        """Calculate overall confidence from step confidences."""
        if not step_results:
            return 0.0
        
        total_confidence = sum(result.confidence for result in step_results.values())
        return total_confidence / len(step_results)
    
    def _calculate_create_compliance(
        self, 
        prompt: str, 
        step_results: Dict[EvaluationStep, EvaluationResult]
    ) -> float:
        """Calculate CREATE framework compliance score."""
        compliance_score = 70.0  # Base compliance
        
        # Check CREATE component presence
        create_components = [
            "C - Context", "R - Request", "E - Examples", 
            "A - Augmentations", "T - Tone", "E - Evaluation"
        ]
        present_components = sum(1 for comp in create_components if comp in prompt)
        compliance_score += (present_components / len(create_components)) * 30
        
        # Adjust based on evaluation results
        verification_issues = sum(
            1 for result in step_results.values() 
            if DiagnosticFlag.VERIFICATION_ISSUE in result.flags
        )
        compliance_score -= verification_issues * 5
        
        return min(max(compliance_score, 0.0), 100.0)
    
    def _identify_critical_issues(self, evaluation: ComprehensiveEvaluation) -> List[str]:
        """Identify critical issues requiring immediate attention."""
        critical_issues = []
        
        # Safety concerns are always critical
        if DiagnosticFlag.SAFETY_CONCERN in evaluation.all_flags:
            critical_issues.append("Safety concerns identified - requires immediate review")
        
        # Multiple verification issues indicate systemic problems
        verification_count = sum(
            1 for result in evaluation.step_results.values()
            if DiagnosticFlag.VERIFICATION_ISSUE in result.flags
        )
        if verification_count >= 3:
            critical_issues.append("Multiple verification issues detected - prompt structure needs revision")
        
        # Very low scores indicate fundamental problems
        low_scoring_steps = [
            step.value for step, result in evaluation.step_results.items()
            if result.score < 40.0
        ]
        if len(low_scoring_steps) >= 2:
            critical_issues.append(f"Multiple low-scoring evaluation steps: {', '.join(low_scoring_steps)}")
        
        return critical_issues
    
    def _generate_improvement_recommendations(self, evaluation: ComprehensiveEvaluation) -> List[str]:
        """Generate actionable improvement recommendations."""
        recommendations = []
        
        # Collect all step recommendations
        for result in evaluation.step_results.values():
            recommendations.extend(result.recommendations)
        
        # Add overall recommendations based on flags
        if DiagnosticFlag.EXPERT_JUDGMENT in evaluation.all_flags:
            recommendations.append("Consider adding explicit sourcing for expert judgment claims")
        
        if evaluation.compliance_score < 80:
            recommendations.append("Enhance CREATE framework component completeness and quality")
        
        if evaluation.overall_confidence < 70:
            recommendations.append("Improve evaluation confidence through more specific requirements")
        
        # Remove duplicates and sort by priority
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Limit to top 10 recommendations
    
    def _create_error_evaluation(self, error_message: str, rigor_level: RigorLevel) -> ComprehensiveEvaluation:
        """Create error evaluation when assessment fails."""
        return ComprehensiveEvaluation(
            overall_score=0.0,
            overall_confidence=0.0,
            rigor_level=rigor_level,
            critical_issues=[f"Evaluation failed: {error_message}"],
            improvement_recommendations=["Fix evaluation system error before retrying assessment"]
        )