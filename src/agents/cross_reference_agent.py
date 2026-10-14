import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm.azure_client import get_llm
from src.schemas.review import AgentOutput, Finding, Severity, Category, ReviewResult

SYSTEM_PROMPT = (
    "You are a senior software architect reviewing a multi-file codebase for cross-file issues. "
    "You focus on problems that only appear when analyzing how files interact:\n"
    "- Circular imports or missing imports between modules\n"
    "- Functions called with wrong arguments or calling functions that don't exist in other files\n"
    "- Inconsistent data contracts (e.g., one file returns a dict, another expects a list)\n"
    "- Shared mutable state accessed from multiple files without synchronization\n"
    "- Duplicate logic reimplemented across files\n"
    "- Tight coupling between modules that should be independent\n\n"
    "Do NOT repeat issues already found in per-file reviews. Only report cross-file issues.\n"
    "Rate severity as 'critical' for bugs that will crash at runtime, 'warning' for "
    "design problems, 'info' for improvement suggestions."
)


class CrossReferenceAgent:
    def __init__(self):
        self.llm = get_llm()

    async def analyze(
        self,
        files: dict[str, str],
        file_reviews: dict[str, ReviewResult],
    ) -> AgentOutput:
        # Build file listing for prompt
        files_text = ""
        for fname, code in files.items():
            files_text += f"### {fname}\n```\n{code}\n```\n\n"

        # Build Level 1 summary for context
        summaries_text = ""
        for fname, review in file_reviews.items():
            titles = ", ".join(f.title for f in review.findings[:5])
            summaries_text += f"- **{fname}**: {review.summary}"
            if titles:
                summaries_text += f" (top issues: {titles})"
            summaries_text += "\n"

        human_prompt = (
            f"## Per-File Review Summaries (Level 1)\n{summaries_text}\n\n"
            f"## All Files\n{files_text}\n"
            "Analyze how these files interact. Return your findings as a JSON array. "
            "Each finding must have:\n"
            '  "severity": "critical" | "warning" | "info"\n'
            '  "category": "architecture"\n'
            '  "title": short description\n'
            '  "description": detailed explanation referencing specific files\n'
            '  "suggestion": how to fix it\n'
            '  "file_name": primary file affected (or null if systemic)\n\n'
            "If no cross-file issues found, return an empty array: []\n"
            "Return ONLY valid JSON, no markdown fences."
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        return self._parse_response(response.content)

    def _parse_response(self, raw: str) -> AgentOutput:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            findings_data = json.loads(raw)
        except json.JSONDecodeError:
            return AgentOutput(agent_name="cross_reference_agent", findings=[], raw_reasoning=raw)

        findings = []
        for f in findings_data:
            try:
                findings.append(Finding(
                    agent_name="cross_reference_agent",
                    severity=Severity(f.get("severity", "info")),
                    category=Category(f.get("category", "architecture")),
                    title=f.get("title", "Untitled"),
                    description=f.get("description", ""),
                    line_number=f.get("line_number"),
                    suggestion=f.get("suggestion", ""),
                    file_name=f.get("file_name"),
                ))
            except (ValueError, KeyError):
                continue

        return AgentOutput(agent_name="cross_reference_agent", findings=findings, raw_reasoning=raw)
