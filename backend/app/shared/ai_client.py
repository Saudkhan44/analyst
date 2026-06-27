"""
AI client for Groq API integration.

Provides interface for LLM interactions using the official Groq SDK.
"""

import json
import logging
from typing import List, Dict, Any

from groq import Groq

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """Client for interacting with Groq API."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize AI client.

        Args:
            api_key: Optional Groq API key.
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = getattr(
            settings,
            "GROQ_MODEL",
            "openai/gpt-oss-120b",
        )

        self.client = Groq(api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """
        Send messages to Groq and return assistant response.

        Args:
            messages: Chat messages
            temperature: Sampling temperature

        Returns:
            Assistant response string.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=2048,
            )

            if (
                completion.choices
                and completion.choices[0].message
                and completion.choices[0].message.content
            ):
                return completion.choices[0].message.content

            raise ValueError("No response received from Groq.")

        except Exception as e:
            logger.exception("Groq API Error")
            raise Exception(str(e))

    def build_context_prompt(
        self,
        question: str,
        dashboard_summary: Dict[str, Any],
        previous_messages: List[Dict[str, str]] | None = None,
    ) -> List[Dict[str, str]]:
        """
        Build conversation context.

        Args:
            question: User question.
            dashboard_summary: Dashboard summary.
            previous_messages: Previous conversation.

        Returns:
            List of chat messages.
        """

        messages: List[Dict[str, str]] = []

        system_prompt = """
You are an expert AI Data Analyst.

You help users understand their uploaded datasets.

Rules:
- Answer ONLY using the provided dataset context.
- If information is unavailable, clearly say so.
- Do not invent data.
- Keep responses concise.
- Use bullet points whenever appropriate.
- Explain calculations clearly.
"""

        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

        context = f"""
Dataset Context

{json.dumps(dashboard_summary, indent=2)}

Use ONLY this information while answering.
"""

        messages.append(
            {
                "role": "system",
                "content": context,
            }
        )

        if previous_messages:
            messages.extend(previous_messages)

        messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        return messages