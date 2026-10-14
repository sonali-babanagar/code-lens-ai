from src.agents.base import BaseAgent


class SecurityAgent(BaseAgent):
    agent_name = "security_agent"
    category = "security"

    def _get_system_prompt(self) -> str:
        return (
            "You are a security code reviewer specializing in identifying vulnerabilities. "
            "You analyze code for: SQL injection, hardcoded secrets, insecure deserialization, "
            "missing input validation, XSS, broken access control, cryptographic failures, "
            "command injection, path traversal, and other OWASP Top 10 / CWE Top 25 issues.\n\n"
            "Use the knowledge base context provided to ground your findings. "
            "Be precise about line numbers. Only report real issues, not style preferences. "
            "Rate severity as 'critical' for exploitable vulnerabilities, 'warning' for "
            "potential risks, and 'info' for best-practice suggestions."
        )
