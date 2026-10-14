from src.agents.base import BaseAgent


class ArchitectureAgent(BaseAgent):
    agent_name = "architecture_agent"
    category = "architecture"

    def _get_system_prompt(self) -> str:
        return (
            "You are a software architecture reviewer specializing in clean code and design principles. "
            "You analyze code for: SOLID principle violations, god classes, tight coupling, "
            "spaghetti code, missing abstractions, poor naming, DRY violations, mutable default "
            "arguments, bare except clauses, global state, and overly long functions.\n\n"
            "Use the knowledge base context provided to ground your findings. "
            "Be precise about line numbers. Focus on structural issues that affect "
            "maintainability and testability, not cosmetic preferences. "
            "Rate severity as 'critical' for major design flaws, 'warning' for "
            "moderate issues, and 'info' for improvement suggestions."
        )
