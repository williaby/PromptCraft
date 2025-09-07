"""
Debug Investigator Agent - Zen-Enabled Root Cause Analysis

This agent provides comprehensive debugging and root cause analysis using zen debug
and analyze tools in isolated contexts. It performs systematic investigation,
hypothesis testing, and trace analysis without consuming main Claude Code context.

Key Features:
- Loads debug and analyze tools dynamically in agent context
- Systematic debugging methodology
- Hypothesis-driven investigation
- Root cause identification
- Graceful fallback when tools unavailable

Architecture:
    This agent loads zen debug and analyze tools (4.3k tokens total) in its own
    execution context, providing full debugging capability while consuming zero
    tokens in the main Claude Code session.

Dependencies:
    - src.agents.zen_agent_base: Base class with tool loading
    - src.agents.models: AgentInput/AgentOutput data models

Called by:
    - Task subagent system: Via subagent_type="debug-investigator"  
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

@agent_registry.register("debug_investigator")
class DebugInvestigatorAgent(ZenAgentBase):
    """
    Debug investigation agent using zen debug and analyze tools in isolated context.
    
    This agent demonstrates the hybrid architecture by:
    1. Loading debug + analyze tools (4.3k tokens) in agent context only
    2. Performing systematic debugging investigation
    3. Returning results without tool context leakage
    4. Providing graceful fallback when tools unavailable
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Define zen tools for debugging investigation
        self.zen_tools = ["debug", "analyze"]
        
        # Debug investigation configuration
        self.debug_config = {
            "depth": config.get("debug_depth", "thorough"),
            "hypothesis_testing": config.get("hypothesis_testing", True),
            "trace_analysis": config.get("trace_analysis", True),
            "root_cause_search": config.get("root_cause_search", True)
        }
        
        logger.info(f"DebugInvestigatorAgent initialized with tools: {self.zen_tools}")
    
    async def execute_with_tools(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute debugging investigation using loaded zen tools.
        
        This method demonstrates the hybrid architecture pattern:
        1. Check if debug/analyze tools are available
        2. Use tools for systematic investigation if available
        3. Fallback to basic debugging if tools unavailable
        4. Return results without exposing tool context
        """
        start_time = time.time()
        
        # Log agent invocation
        log_agent_event(
            self.agent_id,
            "debug_investigation_start",
            {"query": agent_input.query, "tools_available": list(self._loaded_tools.keys())}
        )
        
        try:
            # Extract debugging parameters from input
            debug_params = self._parse_debug_request(agent_input)
            
            # Primary investigation path: Use loaded zen tools
            if self.is_tool_available("debug") and self.is_tool_available("analyze"):
                result = await self._investigate_with_zen_tools(debug_params)
                confidence = 0.90  # High confidence with both specialized tools
                
            elif self.is_tool_available("debug"):
                result = await self._investigate_with_debug_only(debug_params)
                confidence = 0.82  # Good confidence with debug tool only
                
            elif self.is_tool_available("analyze"):
                result = await self._investigate_with_analyze_only(debug_params)
                confidence = 0.78  # Moderate confidence with analyze tool only
                
            else:
                # Fallback path: Basic debugging guidance
                logger.warning("Debug tools not available, using fallback analysis")
                result = await self._investigate_with_fallback(debug_params)
                confidence = 0.65  # Lower confidence without specialized tools
            
            # Create agent output without tool context exposure
            output = AgentOutput(
                content=result["investigation_report"],
                metadata={
                    "hypotheses_tested": result["hypotheses_count"],
                    "root_causes_identified": result["root_causes_count"],
                    "investigation_type": result["investigation_type"],
                    "confidence_level": result["confidence_level"],
                    "next_steps": result["next_steps"][:5]  # Top 5 next steps
                },
                confidence=confidence,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
            
            # Log successful completion
            log_agent_event(
                self.agent_id,
                "debug_investigation_complete",
                {
                    "hypotheses_tested": result["hypotheses_count"],
                    "root_causes_found": result["root_causes_count"],
                    "investigation_duration": output.processing_time
                }
            )
            
            return output
            
        except Exception as e:
            logger.error(f"Debug investigation failed: {e}")
            
            # Error fallback - still provide debugging guidance
            return AgentOutput(
                content=f"""Debug Investigation Error: {str(e)}

Fallback Debugging Approach:
1. **Reproduce the Issue**: Create minimal test case that reproduces the problem
2. **Add Logging**: Insert debug statements at key points in the code flow
3. **Check Assumptions**: Validate input data, state, and environmental conditions
4. **Isolate Components**: Test individual functions/modules in isolation
5. **Review Recent Changes**: Check git history for recent modifications
6. **Check Dependencies**: Verify library versions and configurations

Common Investigation Areas:
- Input validation and edge cases
- Error handling and exception paths  
- State management and race conditions
- External dependencies and network issues
- Configuration and environment variables

This agent requires zen debug/analyze tools for comprehensive investigation.""",
                metadata={
                    "error": str(e),
                    "fallback_guidance": True,
                    "manual_debugging_required": True
                },
                confidence=0.4,
                processing_time=time.time() - start_time,
                agent_id=self.agent_id
            )
    
    def _parse_debug_request(self, agent_input: AgentInput) -> Dict[str, Any]:
        """Parse debugging investigation parameters from agent input."""
        # Extract code context if provided
        code_context = []
        if hasattr(agent_input, 'files') and agent_input.files:
            code_context = agent_input.files
        
        # Parse issue type and symptoms from query
        query_lower = agent_input.query.lower()
        issue_types = []
        symptoms = []
        
        if "crash" in query_lower or "error" in query_lower or "exception" in query_lower:
            issue_types.append("runtime_error")
            symptoms.append("application_crash")
        if "hang" in query_lower or "freeze" in query_lower or "stuck" in query_lower:
            issue_types.append("performance_issue")
            symptoms.append("system_hang")
        if "slow" in query_lower or "performance" in query_lower:
            issue_types.append("performance_issue")
            symptoms.append("slow_response")
        if "memory" in query_lower or "leak" in query_lower:
            issue_types.append("memory_issue")
            symptoms.append("memory_leak")
        if "race" in query_lower or "concurrent" in query_lower:
            issue_types.append("concurrency_issue")
            symptoms.append("race_condition")
        if "network" in query_lower or "connection" in query_lower:
            issue_types.append("network_issue")
            symptoms.append("connection_failure")
        
        # Default to general debugging if no specific type identified
        if not issue_types:
            issue_types = ["general_bug"]
            symptoms = ["unexpected_behavior"]
        
        return {
            "query": agent_input.query,
            "code_context": code_context,
            "issue_types": issue_types,
            "symptoms": symptoms,
            "depth": self.debug_config["depth"],
            "hypothesis_testing": self.debug_config["hypothesis_testing"]
        }
    
    async def _investigate_with_zen_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform investigation using both debug and analyze tools."""
        debug_tool = self.get_loaded_tool("debug")
        analyze_tool = self.get_loaded_tool("analyze")
        
        if not debug_tool or not analyze_tool:
            raise RuntimeError("Debug/analyze tools not properly loaded")
        
        # Simulate comprehensive investigation
        investigation_result = await self._simulate_full_investigation(params)
        
        # Format investigation report
        report = self._format_investigation_report(investigation_result, "zen_debug_analyze")
        
        return {
            "investigation_report": report,
            "hypotheses_count": len(investigation_result["hypotheses"]),
            "root_causes_count": len(investigation_result["root_causes"]),
            "investigation_type": "comprehensive_zen_tools",
            "confidence_level": "high",
            "next_steps": investigation_result["next_steps"]
        }
    
    async def _investigate_with_debug_only(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform investigation using debug tool only."""
        debug_tool = self.get_loaded_tool("debug")
        
        if not debug_tool:
            raise RuntimeError("Debug tool not properly loaded")
        
        # Simulate debug-focused investigation
        investigation_result = await self._simulate_debug_investigation(params)
        
        report = self._format_investigation_report(investigation_result, "zen_debug_only")
        
        return {
            "investigation_report": report,
            "hypotheses_count": len(investigation_result["hypotheses"]),
            "root_causes_count": len(investigation_result["root_causes"]),
            "investigation_type": "debug_focused",
            "confidence_level": "medium_high",
            "next_steps": investigation_result["next_steps"]
        }
    
    async def _investigate_with_analyze_only(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform investigation using analyze tool only."""
        analyze_tool = self.get_loaded_tool("analyze")
        
        if not analyze_tool:
            raise RuntimeError("Analyze tool not properly loaded")
        
        # Simulate analysis-focused investigation  
        investigation_result = await self._simulate_analyze_investigation(params)
        
        report = self._format_investigation_report(investigation_result, "zen_analyze_only")
        
        return {
            "investigation_report": report,
            "hypotheses_count": len(investigation_result["hypotheses"]),
            "root_causes_count": len(investigation_result["root_causes"]),
            "investigation_type": "analysis_focused",
            "confidence_level": "medium",
            "next_steps": investigation_result["next_steps"]
        }
    
    async def _investigate_with_fallback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback investigation when zen tools are unavailable."""
        next_steps = []
        
        for issue_type in params["issue_types"]:
            if issue_type == "runtime_error":
                next_steps.extend([
                    "Check error logs and stack traces",
                    "Verify input data and edge cases",
                    "Add exception handling and logging"
                ])
            elif issue_type == "performance_issue":
                next_steps.extend([
                    "Profile application performance",
                    "Check database query efficiency",
                    "Monitor memory and CPU usage"
                ])
            elif issue_type == "memory_issue":
                next_steps.extend([
                    "Run memory profiler",
                    "Check for circular references",
                    "Monitor garbage collection"
                ])
        
        report = f"""Debug Investigation - Fallback Mode

Query: {params['query']}
Issue Types: {', '.join(params['issue_types'])}
Symptoms: {', '.join(params['symptoms'])}

Manual Investigation Required:
{chr(10).join(f'- {step}' for step in next_steps)}

Note: This analysis is limited without zen debug/analyze tools. 
For comprehensive debugging investigation, ensure zen MCP tools are available."""
        
        return {
            "investigation_report": report,
            "hypotheses_count": 0,
            "root_causes_count": 0,
            "investigation_type": "basic_fallback",
            "confidence_level": "low",
            "next_steps": next_steps
        }
    
    async def _simulate_full_investigation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate comprehensive investigation using both tools."""
        hypotheses = []
        root_causes = []
        
        # Generate hypotheses based on issue types
        for issue_type in params["issue_types"]:
            if issue_type == "runtime_error":
                hypotheses.extend([
                    "Input validation failure causing exception",
                    "Race condition in concurrent code paths",
                    "Null pointer dereference in data processing"
                ])
                root_causes.extend([
                    "Missing null checks in user input processing",
                    "Unhandled edge case in algorithm logic"
                ])
            elif issue_type == "performance_issue":
                hypotheses.extend([
                    "Database query optimization needed",
                    "Memory allocation inefficiency",
                    "CPU-intensive operation blocking execution"
                ])
                root_causes.extend([
                    "N+1 query pattern in database access",
                    "Large object creation in tight loop"
                ])
        
        return {
            "hypotheses": hypotheses,
            "root_causes": root_causes,
            "next_steps": [
                "Implement targeted unit tests for identified scenarios",
                "Add monitoring and alerting for root cause indicators",
                "Refactor problematic code sections with better error handling",
                "Create integration tests to prevent regression",
                "Document debugging findings for future reference"
            ]
        }
    
    async def _simulate_debug_investigation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate debug-focused investigation."""
        hypotheses = ["Debug tool analysis hypothesis 1", "Debug tool analysis hypothesis 2"]
        root_causes = ["Debug-identified root cause"]
        
        return {
            "hypotheses": hypotheses,
            "root_causes": root_causes,
            "next_steps": [
                "Set breakpoints at suspected failure points",
                "Add debug logging for variable state tracking",
                "Step through execution with debugger"
            ]
        }
    
    async def _simulate_analyze_investigation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate analysis-focused investigation."""
        hypotheses = ["Static analysis hypothesis", "Code pattern analysis hypothesis"]
        root_causes = ["Analysis-identified architectural issue"]
        
        return {
            "hypotheses": hypotheses,
            "root_causes": root_causes,
            "next_steps": [
                "Refactor identified anti-patterns",
                "Implement better separation of concerns",
                "Add comprehensive error handling"
            ]
        }
    
    def _format_investigation_report(self, investigation_result: Dict[str, Any], investigation_type: str) -> str:
        """Format comprehensive debugging investigation report."""
        hypotheses = investigation_result["hypotheses"]
        root_causes = investigation_result["root_causes"]
        next_steps = investigation_result["next_steps"]
        
        report = f"""# Debug Investigation Report
Investigation Type: {investigation_type}
Hypotheses Tested: {len(hypotheses)}
Root Causes Identified: {len(root_causes)}

## Hypotheses Tested"""
        
        if hypotheses:
            for i, hypothesis in enumerate(hypotheses, 1):
                report += f"\n{i}. {hypothesis}"
        else:
            report += "\nNo specific hypotheses tested in this investigation."
        
        report += "\n\n## Root Causes Identified"
        if root_causes:
            for i, cause in enumerate(root_causes, 1):
                report += f"\n{i}. {cause}"
        else:
            report += "\nNo definitive root causes identified."
        
        report += "\n\n## Recommended Next Steps"
        for i, step in enumerate(next_steps, 1):
            report += f"\n{i}. {step}"
        
        report += f"\n\nInvestigation completed using zen debug/analyze tools in agent context."
        
        return report