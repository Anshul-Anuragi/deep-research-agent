"""
Coordinator Agent - Plans the research and creates subtopics
"""

import json
import re
from datetime import date
from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

from prompts.coordinator_prompt import COORDINATOR_SYSTEM_PROMPT
from tools.research_tools import extract_text
from agents.llm_factory import get_llm

load_dotenv()


class Coordinator:
    def __init__(self, model: str = None):
        self.llm = get_llm(model=model, temperature=0.2)
        self.max_researchers = int(os.getenv("DR_MAX_RESEARCHERS", "3"))

    def _clean_json(self, text: Any) -> dict:
        """Extract and parse JSON from LLM response"""
        text = extract_text(text).strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        return {}

    def plan(self, question: str, clarifications: str = "") -> Dict[str, Any]:
        """
        Main method: Analyze question and return research plan
        """
        prompt = COORDINATOR_SYSTEM_PROMPT.format(
            today=date.today().isoformat(),
            question=question,
            clarifications=clarifications or "None",
            max_researchers=self.max_researchers
        )

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Create the research plan now.")
        ]

        response = self.llm.invoke(messages)
        data = self._clean_json(response.content)

        # Safety defaults
        if not data.get("title"):
            data["title"] = "Research Report"
        if not data.get("subtopics"):
            data["subtopics"] = [{
                "topic": "General Research",
                "objective": question,
                "key_questions": [question],
                "suggested_sources": ["Web search", "Recent articles"],
                "constraints": []
            }]

        # Limit number of researchers
        data["subtopics"] = data["subtopics"][:self.max_researchers]

        return data
