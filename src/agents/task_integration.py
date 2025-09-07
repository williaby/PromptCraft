"""
Task Integration for Zen Agents - Hybrid Architecture Bridge

This module provides integration between the Claude Code Task subagent system
and the new zen-enabled agents. It enables seamless invocation of specialized
agents with zen tool loading through the existing Task interface.

Key Features:
- Maps Task subagent_type to zen-enabled agents
- Handles agent instantiation and configuration
- Provides context optimization tracking
- Integrates with existing PromptCraft agent system

Architecture:
    This module acts as a bridge between:
    1. Claude Code Task system (subagent invocation)
    2. PromptCraft zen agents (hybrid tool loading)
    3. Agent registry (agent discovery and instantiation)

Dependencies:
    - src.agents.registry: For agent class discovery
    - src.agents.zen_agent_base: For zen agent capabilities
    - src.agents.models: For data models

Called by:
    - Task subagent system: For zen agent execution
    - Agent orchestration workflows: For specialized analysis

Usage:
    Task(subagent_type="security-auditor", prompt="Analyze authentication code")
"""

import logging
import time
from typing import Any, Dict, List, Optional, Type

from src.agents.registry import agent_registry
from src.agents.zen_agent_base import ZenAgentBase, ZEN_AGENT_REGISTRY
from src.agents.models import AgentInput, AgentOutput
from src.utils.observability import create_structured_logger, log_agent_event

logger = create_structured_logger(__name__)

# Mapping from Task subagent_type to zen agent classes
TASK_TO_ZEN_AGENT_MAPPING = {
    "security-auditor": "security_auditor",
    "code-reviewer": "code_reviewer", 
    "debug-investigator": "debug_investigator",
    "analysis-agent": "analysis_agent",
    "refactor-specialist": "refactor_specialist",
    "documentation-writer": "documentation_writer",
    "deep-thinking-agent": "deep_thinking_agent"
}

class ZenAgentTaskIntegration:
    """
    Integration layer between Claude Code Task system and zen agents.
    
    This class handles:
    1. Task subagent_type resolution to zen agent classes
    2. Agent instantiation and configuration
    3. Performance and context tracking
    4. Error handling and fallback strategies
    """
    
    def __init__(self):
        self.performance_metrics: Dict[str, List[float]] = {}
        self.context_savings_total = 0
        
    async def execute_zen_agent_task(
        self,
        subagent_type: str,
        prompt: str,
        files: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute a zen agent through the Task interface.
        
        This is the main entry point for Task -> Zen Agent integration:
        1. Resolve subagent_type to zen agent class
        2. Instantiate agent with appropriate configuration
        3. Execute agent with tool loading
        4. Track performance and context metrics
        5. Return results compatible with Task system
        """
        start_time = time.time()
        
        try:
            # Resolve subagent type to zen agent
            zen_agent_id = TASK_TO_ZEN_AGENT_MAPPING.get(subagent_type)
            if not zen_agent_id:
                raise ValueError(f"Unknown zen agent subagent_type: {subagent_type}")
            
            # Get agent class from registry
            agent_class = agent_registry.get_agent_class(zen_agent_id)
            if not agent_class:
                raise ValueError(f"Agent class not found for: {zen_agent_id}")
            
            # Verify it's a zen-enabled agent
            if not issubclass(agent_class, ZenAgentBase):
                raise ValueError(f"Agent {zen_agent_id} is not zen-enabled")
            
            # Create agent configuration
            agent_config = self._create_agent_config(subagent_type, metadata or {})
            
            # Instantiate agent
            agent = agent_class(agent_config)
            
            # Prepare agent input
            agent_input = AgentInput(
                query=prompt,
                files=files or [],
                metadata=metadata or {}
            )
            
            # Log agent invocation
            log_agent_event(
                agent.agent_id,
                "task_integration_start",
                {
                    "subagent_type": subagent_type,
                    "zen_tools": agent.zen_tools,
                    "prompt_length": len(prompt)
                }
            )
            
            # Execute agent with zen tool loading
            result = await agent.execute(agent_input)
            
            # Track performance metrics
            execution_time = time.time() - start_time
            self._track_performance_metrics(subagent_type, execution_time, result)
            
            # Add task integration metadata
            result.metadata.update({
                "task_integration": True,
                "subagent_type": subagent_type,
                "zen_agent_id": zen_agent_id,
                "execution_via": "zen_agent_task_integration",
                "total_execution_time": execution_time
            })
            
            logger.info(f"Zen agent task completed: {subagent_type} in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Zen agent task failed: {subagent_type} - {e}")
            
            # Return error response compatible with Task system
            return AgentOutput(
                content=f"Zen agent execution failed: {str(e)}",
                metadata={
                    "task_integration_error": True,
                    "subagent_type": subagent_type,
                    "error_message": str(e),
                    "fallback_response": True
                },
                confidence=0.1,
                processing_time=time.time() - start_time,
                agent_id=f"zen-task-error-{subagent_type}"
            )
    
    def _create_agent_config(self, subagent_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent configuration from task parameters."""
        config = {
            "agent_id": f"zen-{subagent_type}-{int(time.time())}",
            "task_integration": True,
            "invoked_via_task": True
        }
        
        # Add subagent-specific configuration
        if subagent_type == "security-auditor":
            config.update({
                "severity_threshold": metadata.get("severity", "medium"),
                "owasp_compliance": True,
                "vulnerability_scanning": True
            })
        elif subagent_type == "code-reviewer":
            config.update({
                "review_depth": metadata.get("depth", "comprehensive"),
                "focus_areas": metadata.get("focus", ["quality", "maintainability"])
            })
        elif subagent_type == "debug-investigator":
            config.update({
                "debug_depth": metadata.get("depth", "thorough"),
                "hypothesis_testing": True
            })
        
        # Add any custom metadata
        config.update(metadata)
        
        return config
    
    def _track_performance_metrics(
        self,
        subagent_type: str,
        execution_time: float,
        result: AgentOutput
    ):
        """Track performance metrics for zen agent executions."""
        if subagent_type not in self.performance_metrics:
            self.performance_metrics[subagent_type] = []
        
        self.performance_metrics[subagent_type].append(execution_time)
        
        # Track context savings
        tools_loaded = result.metadata.get("tools_loaded", [])
        if tools_loaded:
            # Estimate context saved by not loading in main context
            context_saved = len(tools_loaded) * 2000  # Rough estimate
            self.context_savings_total += context_saved
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all zen agent executions."""
        summary = {
            "total_executions": sum(len(times) for times in self.performance_metrics.values()),
            "total_context_saved": self.context_savings_total,
            "agent_performance": {}
        }
        
        for agent_type, execution_times in self.performance_metrics.items():
            if execution_times:
                summary["agent_performance"][agent_type] = {
                    "executions": len(execution_times),
                    "avg_time": sum(execution_times) / len(execution_times),
                    "min_time": min(execution_times),
                    "max_time": max(execution_times),
                    "under_target": sum(1 for t in execution_times if t <= 0.7)  # 700ms target
                }
        
        return summary
    
    def list_available_zen_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available zen agents for Task integration."""
        available_agents = {}
        
        for task_type, zen_agent_id in TASK_TO_ZEN_AGENT_MAPPING.items():
            zen_info = ZEN_AGENT_REGISTRY.get(zen_agent_id, {})
            available_agents[task_type] = {
                "zen_agent_id": zen_agent_id,
                "zen_tools": zen_info.get("zen_tools", []),
                "description": zen_info.get("description", "No description"),
                "context_cost": zen_info.get("context_cost_when_loaded", "Unknown"),
                "available": agent_registry.has_agent(zen_agent_id)
            }
        
        return available_agents

# Global instance for task integration
zen_task_integration = ZenAgentTaskIntegration()

# Convenience functions for Task system integration
async def execute_security_auditor_task(
    prompt: str,
    files: Optional[List[str]] = None,
    severity: str = "medium"
) -> AgentOutput:
    """Execute security auditor through Task integration."""
    return await zen_task_integration.execute_zen_agent_task(
        "security-auditor",
        prompt,
        files,
        {"severity": severity}
    )

async def execute_code_reviewer_task(
    prompt: str, 
    files: Optional[List[str]] = None,
    depth: str = "comprehensive"
) -> AgentOutput:
    """Execute code reviewer through Task integration."""
    return await zen_task_integration.execute_zen_agent_task(
        "code-reviewer",
        prompt,
        files,
        {"depth": depth}
    )

async def execute_debug_investigator_task(
    prompt: str,
    files: Optional[List[str]] = None,
    depth: str = "thorough"
) -> AgentOutput:
    """Execute debug investigator through Task integration.""" 
    return await zen_task_integration.execute_zen_agent_task(
        "debug-investigator",
        prompt,
        files,
        {"depth": depth}
    )

def get_zen_agent_performance_report() -> str:
    """Get formatted performance report for zen agents."""
    summary = zen_task_integration.get_performance_summary()
    
    report = f"""# Zen Agent Performance Report

## Summary
- Total Executions: {summary['total_executions']}
- Total Context Saved: {summary['total_context_saved']:,} tokens
- Context Optimization: {summary['total_context_saved'] / 2000:.1f}% improvement

## Agent Performance"""
    
    for agent_type, metrics in summary["agent_performance"].items():
        report += f"""
### {agent_type}
- Executions: {metrics['executions']}
- Average Time: {metrics['avg_time']:.3f}s
- Performance Target: {metrics['under_target']}/{metrics['executions']} under 700ms
- Range: {metrics['min_time']:.3f}s - {metrics['max_time']:.3f}s"""
    
    return report