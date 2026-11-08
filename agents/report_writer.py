"""
Report Writer Agent - Synthesizes all notes into final report
"""

import os
from datetime import date
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from prompts.report_writer_prompt import REPORT_WRITER_SYSTEM_PROMPT
from tools.research_tools import save_final_report, list_notes, extract_text
from agents.llm_factory import get_llm

load_dotenv()


class ReportWriter:
    def __init__(self, model: str = None):
        self.llm = get_llm(model=model, temperature=0.4)

    def write_report(self, question: str, title: str, notes: Dict[str, Any]) -> str:
        """
        Takes all research notes and writes the final report.
        """
        # Combine all notes
        combined_notes = "\n\n---\n\n".join(
            f"### Notes from: {topic}\n\n{extract_text(content)}" 
            for topic, content in notes.items()
        )

        system_prompt = REPORT_WRITER_SYSTEM_PROMPT.format(
            question=question,
            today=date.today().isoformat()
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Here are the research notes:\n\n{combined_notes}\n\nPlease write the final report now.")
        ]

        response = self.llm.invoke(messages)
        report = extract_text(response.content)

        # Save final report
        saved_path = save_final_report(title, report)
        print(f"\n✅ Final report saved: {saved_path}")

        return report

