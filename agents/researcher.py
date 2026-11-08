"""
Researcher Agent - Conducts focused research on one subtopic
"""

import os
from datetime import date
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv

from prompts.researcher_prompt import RESEARCHER_SYSTEM_PROMPT
from tools.research_tools import (
    tavily_search,
    wikipedia,
    get_current_date,
    save_research_note,
    extract_text,
)
from agents.llm_factory import get_llm

load_dotenv()


class Researcher:
    def __init__(self, model: str = None):
        self.base_llm = get_llm(model=model, temperature=0.3)
        self.tools = [tavily_search, wikipedia, get_current_date]
        self.tools_map = {
            tavily_search.name: tavily_search,
            "tavily_search": tavily_search,
            "tavily_search_results_json": tavily_search,
            wikipedia.name: wikipedia,
            get_current_date.name: get_current_date,
        }
        self.llm = self.base_llm.bind_tools(self.tools)
        self.max_steps = int(os.getenv("DR_MAX_STEPS", "6"))

    def research(self, title: str, subtopic: Dict[str, Any]) -> str:
        """
        Research one subtopic and return markdown notes.
        Also saves the notes to research_notes/{title}/
        """
        topic = subtopic.get("topic", "Research")
        objective = subtopic.get("objective", "")
        key_questions = subtopic.get("key_questions", [])
        suggested_sources = ", ".join(subtopic.get("suggested_sources", []))
        constraints = ", ".join(subtopic.get("constraints", []))

        key_questions_text = "\n".join(f"- {q}" for q in key_questions)

        system_prompt = RESEARCHER_SYSTEM_PROMPT.format(
            today=date.today().isoformat(),
            topic=topic,
            objective=objective,
            key_questions=key_questions_text,
            suggested_sources=suggested_sources or "Any reputable sources",
            constraints=constraints or "None"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Start researching the topic: {topic}")
        ]

        # Simple ReAct style loop
        for step in range(self.max_steps):
            response = self.llm.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                try:
                    if tool_name in self.tools_map:
                        result = self.tools_map[tool_name].invoke(tool_args)
                    else:
                        result = f"Unknown tool: {tool_name}"
                except Exception as e:
                    result = f"Tool error: {str(e)}"

                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                ))

        # Final notes generation
        final_prompt = "Now write the complete research notes in the required markdown format. Do not call any more tools."
        messages.append(HumanMessage(content=final_prompt))

        final_response = self.base_llm.invoke(messages)
        notes = extract_text(final_response.content)

        # Save researcher's notes
        save_research_note(title, topic, notes)

        return notes
