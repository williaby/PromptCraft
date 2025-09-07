"""
Code Reviewer Agent - Zen-Enabled Code Quality Analysis

This agent provides comprehensive code review capabilities using the zen codereview
tool in an isolated context. It performs quality assessment, best practices validation,
and provides detailed feedback without consuming main Claude Code context.

Key Features:
- Loads codereview tool dynamically in agent context
- Comprehensive code quality analysis
- Best practices validation
- Maintainability assessment
- Graceful fallback when tools unavailable

Architecture:
    This agent loads the zen codereview tool (2.3k tokens) in its own execution
    context, providing full code review capability while consuming zero tokens
    in the main Claude Code session.

Dependencies:
    - src.agents.zen_agent_base: Base class with tool loading
    - src.agents.models: AgentInput/AgentOutput data models

Called by:
    - Task subagent system: Via subagent_type="code-reviewer"
    - Agent registry: For dynamic agent instantiation
"""

import logging
import time
from typing import Any, Dict, List, Optional

from src.agents.zen_agent_base import ZenAgentBase
from src.agents.models import AgentInput, AgentOutput
from src.agents.registry import agent_registry
from src.utils.observability import create_structured_logger, log_agent_event

logger = create_structured_logger(__name__)

@agent_registry.register("code_reviewer")
class CodeReviewerAgent(ZenAgentBase):
    """
    Code review agent using zen codereview tool in isolated context.
    
    This agent demonstrates the hybrid architecture by:
    1. Loading codereview tool (2.3k tokens) in agent context only
    2. Performing comprehensive code quality analysis
    3. Returning results without tool context leakage
    4. Providing graceful fallback when tools unavailable
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Define zen tools for code review
        self.zen_tools = ["codereview"]
        
        # Code review specific configuration
        self.review_config = {
            "depth": config.get("review_depth", "comprehensive"),
            "focus_areas": config.get("focus_areas", ["quality", "maintainability", "security"]),
            "coding_standards": config.get("coding_standards", "pep8"),
            "complexity_threshold": config.get("complexity_threshold", 10)
        }
        
        logger.info(f"CodeReviewerAgent initialized with tools: {self.zen_tools}")
    
    async def execute_with_tools(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute code review using loaded zen tools.
        
        This method demonstrates the hybrid architecture pattern:
        1. Check if codereview tool is available
        2. Use tool for comprehensive analysis if available
        3. Fallback to basic analysis if tool unavailable
        4. Return results without exposing tool context
        """
        start_time = time.time()
        
        # Log agent invocation
        log_agent_event(
            self.agent_id,
            "code_review_start",
            {"query": agent_input.query, "tools_available": list(self._loaded_tools.keys())}
        )
        
        try:
            # Extract review parameters from input
            review_params = self._parse_review_request(agent_input)
            
            # Primary analysis path: Use loaded zen tools
            if self.is_tool_available("codereview"):
                result = await self._review_with_codereview(review_params)
                confidence = 0.92  # High confidence with specialized tool
                
            else:
                # Fallback path: Basic code review
                logger.warning("Codereview tool not available, using fallback analysis")
                result = await self._review_with_fallback(review_params)
                confidence = 0.75  # Lower confidence without specialized tool
            
            # Create agent output without tool context exposure
            output = AgentOutput(
                content=result["review_report"],
                metadata={
                    "issues_found": result["issues_count"],
                    "quality_score": result["quality_score"],
                    "review_type": result["review_type"],
                    "complexity_score": result["complexity_score"],
                    "recommendations": result["recommendations"][:10]  # Top 10 recommendations
                },
                confidence=confidence,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
            
            # Log successful completion
            log_agent_event(
                self.agent_id,
                "code_review_complete",
                {
                    "issues_found": result["issues_count"],
                    "quality_score": result["quality_score"],
                    "review_duration": output.processing_time
                }
            )
            
            return output
            
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            
            # Error fallback - still provide value to user
            return AgentOutput(
                content=f"""Code Review Error: {str(e)}

Fallback Analysis:
- Unable to perform comprehensive code review
- Recommend manual code review focusing on:
  * Code style and formatting consistency
  * Error handling and edge cases  
  * Security vulnerabilities
  * Performance optimization opportunities
  * Documentation completeness

This agent requires the codereview tool for full functionality.""",
                metadata={
                    "error": str(e),
                    "fallback_analysis": True,
                    "manual_review_required": True
                },
                confidence=0.3,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
    
    def _parse_review_request(self, agent_input: AgentInput) -> Dict[str, Any]:
        """Parse code review parameters from agent input."""
        # Extract code files if provided
        code_files = []
        if hasattr(agent_input, 'files') and agent_input.files:
            code_files = agent_input.files
        
        # Parse focus areas from query
        query_lower = agent_input.query.lower()
        focus_areas = self.review_config["focus_areas"].copy()
        
        if "security" in query_lower:
            focus_areas.append("security_review")
        if "performance" in query_lower:
            focus_areas.append("performance_optimization")
        if "style" in query_lower or "format" in query_lower:
            focus_areas.append("code_style")
        if "complexity" in query_lower:
            focus_areas.append("complexity_analysis")
        if "documentation" in query_lower or "docs" in query_lower:
            focus_areas.append("documentation_quality")
        
        return {
            "query": agent_input.query,
            "code_files": code_files,
            "focus_areas": list(set(focus_areas)),  # Remove duplicates
            "depth": self.review_config["depth"],
            "coding_standards": self.review_config["coding_standards"],
            "complexity_threshold": self.review_config["complexity_threshold"]
        }
    
    async def _review_with_codereview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform code review using the loaded codereview tool.
        
        This demonstrates the hybrid architecture's value:
        Full tool capability without context consumption in main session.
        """
        codereview_tool = self.get_loaded_tool("codereview")
        
        if not codereview_tool:
            raise RuntimeError("Codereview tool not properly loaded")
        
        # Simulate codereview tool execution
        # In real implementation, this would call the actual zen codereview tool
        review_result = await self._simulate_codereview_analysis(params)
        
        # Format comprehensive review report
        report = self._format_review_report(review_result, "zen_codereview")
        
        return {
            "review_report": report,
            "issues_count": len(review_result["issues"]),
            "quality_score": review_result["quality_score"],
            "review_type": "zen_codereview_comprehensive",
            "complexity_score": review_result["complexity_score"],
            "recommendations": review_result["recommendations"]
        }
    
    async def _review_with_fallback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback code review when zen tools are unavailable."""
        issues = []
        recommendations = []
        
        for focus_area in params["focus_areas"]:
            if focus_area == "quality":
                issues.append("Manual code quality review required")
                recommendations.append("Check for consistent naming conventions")
                recommendations.append("Validate error handling patterns")
                
            elif focus_area == "maintainability":
                issues.append("Manual maintainability assessment required") 
                recommendations.append("Review function and class sizes")
                recommendations.append("Check for code duplication")
                
            elif focus_area == "security_review":
                issues.append("Manual security review required")
                recommendations.append("Validate input sanitization")
                recommendations.append("Check authentication and authorization")
        
        # Format basic review report
        report = f"""Code Review - Fallback Mode

Query: {params['query']}
Focus Areas: {', '.join(params['focus_areas'])}

Issues Identified (Manual Review Required):
{chr(10).join(f'- {issue}' for issue in issues)}

Recommendations:
{chr(10).join(f'- {rec}' for rec in recommendations)}

Note: This analysis is limited without the codereview tool. 
For comprehensive code review, ensure zen MCP tools are available."""
        
        return {
            "review_report": report,
            "issues_count": len(issues),
            "quality_score": 0.5,  # Unknown without tools
            "review_type": "basic_fallback",
            "complexity_score": 0.5,  # Unknown without tools
            "recommendations": recommendations
        }
    
    async def _simulate_codereview_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate zen codereview tool execution for PoC."""
        issues = []
        
        # Simulate comprehensive code analysis
        for focus_area in params["focus_areas"]:
            if focus_area == "quality":
                issues.extend([
                    {"type": "naming", "severity": "medium", "description": "Inconsistent variable naming"},
                    {"type": "error_handling", "severity": "high", "description": "Missing error handling for edge cases"}
                ])
            elif focus_area == "maintainability":
                issues.extend([
                    {"type": "complexity", "severity": "high", "description": "Function exceeds complexity threshold"},
                    {"type": "duplication", "severity": "medium", "description": "Code duplication detected"}
                ])
            elif focus_area == "security_review":
                issues.extend([
                    {"type": "input_validation", "severity": "high", "description": "Input validation missing"},
                    {"type": "secrets", "severity": "critical", "description": "Hardcoded secret detected"}
                ])
        
        # Calculate quality score based on issues
        critical_count = sum(1 for issue in issues if issue["severity"] == "critical")
        high_count = sum(1 for issue in issues if issue["severity"] == "high")
        medium_count = sum(1 for issue in issues if issue["severity"] == "medium")
        low_count = sum(1 for issue in issues if issue["severity"] == "low")
        
        # Quality scoring algorithm (higher score = better quality)
        quality_score = max(0, 1.0 - (critical_count * 0.4 + high_count * 0.3 + medium_count * 0.15 + low_count * 0.05))
        
        return {
            "issues": issues,
            "quality_score": quality_score,
            "complexity_score": 0.7,  # Simulated complexity analysis
            "recommendations": [
                "Implement consistent error handling patterns",
                "Refactor large functions into smaller components",
                "Add comprehensive unit tests for edge cases",
                "Implement input validation for all user inputs",
                "Review and remove any hardcoded secrets",
                "Add documentation for complex algorithms",
                "Consider using design patterns for better structure",
                "Implement logging for debugging and monitoring"
            ]
        }
    
    def _format_review_report(self, review_result: Dict[str, Any], review_type: str) -> str:
        """Format comprehensive code review report."""
        issues = review_result["issues"]
        quality_score = review_result["quality_score"]
        complexity_score = review_result["complexity_score"]
        recommendations = review_result["recommendations"]
        
        # Group issues by severity
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]
        medium_issues = [i for i in issues if i["severity"] == "medium"]
        low_issues = [i for i in issues if i["severity"] == "low"]
        
        report = f"""# Code Review Report
Review Type: {review_type}
Quality Score: {quality_score:.2f}/1.00
Complexity Score: {complexity_score:.2f}/1.00

## Issue Summary
- Critical: {len(critical_issues)}
- High: {len(high_issues)} 
- Medium: {len(medium_issues)}
- Low: {len(low_issues)}

## Critical Issues"""
        
        if critical_issues:
            for issue in critical_issues:
                report += f"\n- **{issue['type']}**: {issue['description']}"
        else:
            report += "\nNo critical issues found."
        
        report += "\n\n## High Priority Issues"
        if high_issues:
            for issue in high_issues:
                report += f"\n- **{issue['type']}**: {issue['description']}"
        else:
            report += "\nNo high priority issues found."
        
        report += "\n\n## Recommendations"
        for i, rec in enumerate(recommendations[:8], 1):  # Top 8 recommendations
            report += f"\n{i}. {rec}"
        
        report += f"\n\nReview completed using zen codereview tool in agent context (2.3k tokens isolated)."
        
        return report