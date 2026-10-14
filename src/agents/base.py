import json
from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm.azure_client import get_llm
from src.rag.retriever import KnowledgeRetriever
from src.schemas.review import AgentOutput, Finding, Severity, Category


class BaseAgent(ABC):
    agent_name: str
    category: str

    def __init__(self, retriever: KnowledgeRetriever):
        self.retriever = retriever
        self.llm = get_llm()

    @abstractmethod
    def _get_system_prompt(self) -> str: ...

    def _get_rag_category(self) -> str:
        return self.category

    async def analyze(self, code: str, language: str, file_name: str | None = None) -> AgentOutput:
        context_docs = self.retriever.retrieve(
            query=code[:500],
            category=self._get_rag_category(),
            top_k=5,
        )
        context_text = "\n---\n".join(doc.page_content for doc in context_docs)

        human_prompt = (
            f"## Knowledge Base Context\n{context_text}\n\n"
            f"## Code to Review (language: {language})\n```{language}\n{code}\n```\n\n"
            "Return your findings as a JSON array. Each finding must have:\n"
            '  "severity": "critical" | "warning" | "info"\n'
            f'  "category": "{self.category}"\n'
            '  "title": short description\n'
            '  "description": detailed explanation\n'
            '  "line_number": line number or null\n'
            '  "suggestion": how to fix it\n'
            '  "source_reference": which knowledge base concept this relates to, or null\n\n'
            "If no issues found, return an empty array: []\n"
            "Return ONLY valid JSON, no markdown fences."
        )

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=human_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        return self._parse_response(response.content, file_name=file_name)

    def _parse_response(self, raw: str, file_name: str | None = None) -> AgentOutput:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            findings_data = json.loads(raw)
        except json.JSONDecodeError:
            return AgentOutput(agent_name=self.agent_name, findings=[], raw_reasoning=raw)

        findings = []
        for f in findings_data:
            try:
                findings.append(Finding(
                    agent_name=self.agent_name,
                    severity=Severity(f.get("severity", "info")),
                    category=Category(f.get("category", self.category)),
                    title=f.get("title", "Untitled"),
                    description=f.get("description", ""),
                    line_number=f.get("line_number"),
                    suggestion=f.get("suggestion", ""),
                    source_reference=f.get("source_reference"),
                    file_name=file_name,
                ))
            except (ValueError, KeyError):
                continue

        return AgentOutput(agent_name=self.agent_name, findings=findings, raw_reasoning=raw)
