from typing import Any

from .base_agent import BaseAgent
from .models import AgentInput, AgentOutput


class QwenTestEngineerAgent(BaseAgent):
    """Lightweight stub for QwenTestEngineerAgent to satisfy imports in tests.

    This stub implements only the minimal surface used by unit tests.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.agent_id = config.get("agent_id", "qwen_test_engineer")
        self.default_test_type = config.get("default_test_type", "unit")
        self.coverage_target = config.get("coverage_target", 80.0)
        self.timeout = config.get("timeout", 30)

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "operations": ["generate_tests", "run_tests"],
        }

    def _get_test_file_path(self, src_path: str, test_type: str) -> str:
        if test_type == "unit":
            # naive mapping for the stub
            parts = src_path.split("/")
            domain = parts[1] if len(parts) > 2 else "core"
            name = parts[-1].replace(".py", "")
            return f"tests/unit/{domain}/test_{name}.py"
        parts = src_path.split("/")
        domain = parts[1] if len(parts) > 2 else "api"
        name = parts[-1].replace(".py", "")
        return f"tests/integration/{domain}/test_{name}.py"

    def _create_test_skeleton(self, src_path: str, test_type: str) -> str:
        class_name = src_path.split("/")[-1].replace(".py", "").title().replace("_", "")
        return (
            f"import pytest\n\nclass Test{class_name}:\n    def test_basic_functionality(self):\n        assert True\n"
        )

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        if agent_input.content == "help":
            return AgentOutput(
                content=("Qwen Test Engineer Agent Help\n\n## Available Tasks\n- generate_tests\n- run_tests\n"),
                confidence=1.0,
                processing_time=0.1,
                agent_id=self.agent_id,
            )
        return AgentOutput(content="ok", confidence=0.5, processing_time=0.1, agent_id=self.agent_id)
