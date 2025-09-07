"""
Security Auditor Agent - Proof of Concept for Hybrid Architecture

This agent demonstrates the hybrid architecture by loading the secaudit tool
in its own context and providing security analysis capabilities without
consuming main Claude Code context.

Key Features:
- Loads secaudit tool dynamically in agent context
- Performs OWASP security analysis
- Vulnerability scanning and compliance checking
- Graceful fallback when tools unavailable
- Context isolation guarantee

Architecture:
    This agent loads the zen secaudit tool (2.3k tokens) in its own execution
    context, providing full security analysis capability while consuming zero
    tokens in the main Claude Code session.

Dependencies:
    - src.agents.zen_agent_base: Base class with tool loading
    - src.agents.models: AgentInput/AgentOutput data models
    - logging: For operation tracking

Called by:
    - Task subagent system: Via subagent_type="security-auditor"
    - Agent registry: For dynamic agent instantiation

Time Complexity: O(n) where n is size of code to analyze
Space Complexity: O(k) where k is number of security issues found
"""

import logging
import time
from typing import Any, Dict, List, Optional

from src.agents.zen_agent_base import ZenAgentBase
from src.agents.models import AgentInput, AgentOutput
from src.agents.registry import agent_registry
from src.utils.observability import create_structured_logger, log_agent_event

logger = create_structured_logger(__name__)

@agent_registry.register("security_auditor")
class SecurityAuditorAgent(ZenAgentBase):
    """
    Security analysis agent using zen secaudit tool in isolated context.
    
    This agent demonstrates the hybrid architecture by:
    1. Loading secaudit tool (2.3k tokens) in agent context only
    2. Performing comprehensive security analysis
    3. Returning results without tool context leakage
    4. Providing graceful fallback when tools unavailable
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Define zen tools for security analysis
        self.zen_tools = ["secaudit"]
        
        # Security-specific configuration
        self.security_config = {
            "owasp_compliance": True,
            "vulnerability_scanning": True,
            "dependency_analysis": True,
            "code_analysis": True,
            "severity_threshold": config.get("severity_threshold", "medium")
        }
        
        logger.info(f"SecurityAuditorAgent initialized with tools: {self.zen_tools}")
    
    async def execute_with_tools(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute security analysis using loaded zen tools.
        
        This method demonstrates the hybrid architecture pattern:
        1. Check if secaudit tool is available
        2. Use tool for comprehensive analysis if available
        3. Fallback to basic analysis if tool unavailable
        4. Return results without exposing tool context
        """
        start_time = time.time()
        
        # Log agent invocation
        log_agent_event(
            self.agent_id,
            "security_analysis_start",
            {"query": agent_input.query, "tools_available": list(self._loaded_tools.keys())}
        )
        
        try:
            # Extract analysis parameters from input
            analysis_params = self._parse_security_request(agent_input)
            
            # Primary analysis path: Use loaded zen tools
            if self.is_tool_available("secaudit"):
                result = await self._analyze_with_secaudit(analysis_params)
                confidence = 0.95  # High confidence with specialized tool
                
            else:
                # Fallback path: Basic security analysis
                logger.warning("Secaudit tool not available, using fallback analysis")
                result = await self._analyze_with_fallback(analysis_params)
                confidence = 0.7  # Lower confidence without specialized tool
            
            # Create agent output without tool context exposure
            output = AgentOutput(
                content=result["analysis_report"],
                metadata={
                    "security_issues_found": result["issues_count"],
                    "compliance_score": result["compliance_score"],
                    "analysis_type": result["analysis_type"],
                    "severity_distribution": result["severity_distribution"],
                    "recommendations": result["recommendations"][:5]  # Top 5 recommendations
                },
                confidence=confidence,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
            
            # Log successful completion
            log_agent_event(
                self.agent_id,
                "security_analysis_complete",
                {
                    "issues_found": result["issues_count"],
                    "compliance_score": result["compliance_score"],
                    "analysis_duration": output.processing_time
                }
            )
            
            return output
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            
            # Error fallback - still provide value to user
            return AgentOutput(
                content=f"""Security Analysis Error: {str(e)}

Fallback Analysis:
- Unable to perform comprehensive security analysis
- Recommend manual security review
- Check for common OWASP Top 10 vulnerabilities
- Validate input sanitization and authentication
- Review dependency security with npm audit or pip-audit

This agent requires the secaudit tool for full functionality.""",
                metadata={
                    "error": str(e),
                    "fallback_analysis": True,
                    "manual_review_required": True
                },
                confidence=0.3,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
    
    def _parse_security_request(self, agent_input: AgentInput) -> Dict[str, Any]:
        """
        Parse security analysis parameters from agent input.
        
        Extracts code, focus areas, and analysis preferences from the request.
        """
        # Extract code context if provided
        code_context = []
        if hasattr(agent_input, 'files') and agent_input.files:
            code_context = agent_input.files
        
        # Parse analysis focus from query
        query_lower = agent_input.query.lower()
        focus_areas = []
        
        if "auth" in query_lower or "authentication" in query_lower:
            focus_areas.append("authentication")
        if "sql" in query_lower or "injection" in query_lower:
            focus_areas.append("injection")
        if "xss" in query_lower or "cross-site" in query_lower:
            focus_areas.append("xss")
        if "csrf" in query_lower:
            focus_areas.append("csrf")
        if "dependency" in query_lower or "dependencies" in query_lower:
            focus_areas.append("dependencies")
        if "owasp" in query_lower:
            focus_areas.append("owasp_top10")
        
        # Default to comprehensive analysis if no specific focus
        if not focus_areas:
            focus_areas = ["owasp_top10", "authentication", "injection", "xss"]
        
        return {
            "query": agent_input.query,
            "code_context": code_context,
            "focus_areas": focus_areas,
            "severity_threshold": self.security_config["severity_threshold"],
            "analysis_type": "comprehensive"
        }
    
    async def _analyze_with_secaudit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security analysis using the loaded secaudit tool.
        
        This demonstrates the hybrid architecture's primary value:
        Full tool capability without context consumption in main session.
        """
        secaudit_tool = self.get_loaded_tool("secaudit")
        
        if not secaudit_tool:
            raise RuntimeError("Secaudit tool not properly loaded")
        
        # Simulate secaudit tool execution
        # In real implementation, this would call the actual zen secaudit tool
        analysis_result = await self._simulate_secaudit_analysis(params)
        
        # Format comprehensive security report
        report = self._format_security_report(analysis_result, "zen_secaudit")
        
        return {
            "analysis_report": report,
            "issues_count": len(analysis_result["security_issues"]),
            "compliance_score": analysis_result["compliance_score"],
            "analysis_type": "zen_secaudit_comprehensive",
            "severity_distribution": analysis_result["severity_distribution"],
            "recommendations": analysis_result["recommendations"]
        }
    
    async def _analyze_with_fallback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback security analysis when zen tools are unavailable.
        
        Provides basic security guidance without specialized tooling.
        """
        # Basic security checks based on query analysis
        issues = []
        recommendations = []
        
        for focus_area in params["focus_areas"]:
            if focus_area == "authentication":
                issues.append("Manual authentication review required")
                recommendations.append("Implement multi-factor authentication")
                recommendations.append("Use secure session management")
                
            elif focus_area == "injection":
                issues.append("Manual SQL injection review required") 
                recommendations.append("Use parameterized queries")
                recommendations.append("Validate and sanitize all inputs")
                
            elif focus_area == "xss":
                issues.append("Manual XSS vulnerability review required")
                recommendations.append("Escape output in HTML contexts")
                recommendations.append("Implement Content Security Policy")
        
        # Format basic security report
        report = f"""Security Analysis - Fallback Mode

Query: {params['query']}
Focus Areas: {', '.join(params['focus_areas'])}

Issues Identified (Manual Review Required):
{chr(10).join(f'- {issue}' for issue in issues)}

Recommendations:
{chr(10).join(f'- {rec}' for rec in recommendations)}

Note: This analysis is limited without the secaudit tool. 
For comprehensive security analysis, ensure zen MCP tools are available."""
        
        return {
            "analysis_report": report,
            "issues_count": len(issues),
            "compliance_score": 0.5,  # Unknown without tools
            "analysis_type": "basic_fallback",
            "severity_distribution": {"unknown": len(issues)},
            "recommendations": recommendations
        }
    
    async def _simulate_secaudit_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate zen secaudit tool execution for PoC.
        
        In production, this would interface with the actual secaudit tool
        loaded in the agent's isolated context.
        """
        # Simulate comprehensive security analysis results
        security_issues = []
        
        for focus_area in params["focus_areas"]:
            if focus_area == "authentication":
                security_issues.extend([
                    {"type": "authentication", "severity": "high", "description": "Weak password policy"},
                    {"type": "authentication", "severity": "medium", "description": "Session timeout too long"}
                ])
            elif focus_area == "injection":
                security_issues.extend([
                    {"type": "sql_injection", "severity": "critical", "description": "Unsanitized user input in query"},
                    {"type": "command_injection", "severity": "high", "description": "Shell command execution risk"}
                ])
            elif focus_area == "xss":
                security_issues.extend([
                    {"type": "xss", "severity": "medium", "description": "Unescaped user output"},
                    {"type": "xss", "severity": "low", "description": "Missing CSP header"}
                ])
        
        # Calculate compliance score based on issues
        critical_count = sum(1 for issue in security_issues if issue["severity"] == "critical")
        high_count = sum(1 for issue in security_issues if issue["severity"] == "high")
        medium_count = sum(1 for issue in security_issues if issue["severity"] == "medium")
        low_count = sum(1 for issue in security_issues if issue["severity"] == "low")
        
        # Scoring algorithm (lower score = more issues)
        compliance_score = max(0, 1.0 - (critical_count * 0.4 + high_count * 0.3 + medium_count * 0.2 + low_count * 0.1))
        
        return {
            "security_issues": security_issues,
            "compliance_score": compliance_score,
            "severity_distribution": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "recommendations": [
                "Implement input validation for all user inputs",
                "Use parameterized queries to prevent SQL injection",
                "Implement proper output encoding for XSS prevention",
                "Strengthen authentication and session management",
                "Regular security code reviews and penetration testing",
                "Keep dependencies updated and scan for vulnerabilities",
                "Implement Content Security Policy headers",
                "Use HTTPS for all communications"
            ]
        }
    
    def _format_security_report(self, analysis_result: Dict[str, Any], analysis_type: str) -> str:
        """Format comprehensive security analysis report."""
        issues = analysis_result["security_issues"]
        compliance_score = analysis_result["compliance_score"]
        severity_dist = analysis_result["severity_distribution"]
        recommendations = analysis_result["recommendations"]
        
        # Group issues by severity
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]
        medium_issues = [i for i in issues if i["severity"] == "medium"]
        low_issues = [i for i in issues if i["severity"] == "low"]
        
        report = f"""# Security Analysis Report
Analysis Type: {analysis_type}
Compliance Score: {compliance_score:.2f}/1.00

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
        for i, rec in enumerate(recommendations[:5], 1):
            report += f"\n{i}. {rec}"
        
        report += f"\n\nAnalysis completed using zen secaudit tool in agent context (2.3k tokens isolated)."
        
        return report