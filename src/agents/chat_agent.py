from typing import AsyncGenerator
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm.azure_client import get_llm
from src.schemas.review import ReviewResult
from src.schemas.chat import ChatMessage


class ChatAgent:
    def __init__(self):
        self.llm = get_llm()

    def _build_messages(
        self,
        user_message: str,
        review: ReviewResult,
        chat_history: list[ChatMessage],
    ) -> list:
        findings_text = "\n".join(
            f"- [{f.severity.value}] {f.title}: {f.description} (suggestion: {f.suggestion})"
            for f in review.findings
        )

        system_prompt = (
            "You are a helpful code review assistant. The user submitted code for review "
            "and received findings. Answer their follow-up questions about the findings.\n\n"
            f"## Code Preview\n```\n{review.code_snippet_preview}\n```\n\n"
            f"## Review Findings\n{findings_text}\n\n"
            "Be concise. Reference specific findings by title when relevant. "
            "If the user asks how to fix something, provide a code example."
        )

        messages = [SystemMessage(content=system_prompt)]
        for msg in chat_history[-10:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(SystemMessage(content=msg.content))
        messages.append(HumanMessage(content=user_message))
        return messages

    async def respond(
        self,
        user_message: str,
        review: ReviewResult,
        chat_history: list[ChatMessage],
    ) -> str:
        messages = self._build_messages(user_message, review, chat_history)
        response = await self.llm.ainvoke(messages)
        return response.content

    async def respond_stream(
        self,
        user_message: str,
        review: ReviewResult,
        chat_history: list[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(user_message, review, chat_history)
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
