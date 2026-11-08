"""
Research tools: Web search (Tavily), Wikipedia, File saving
"""

import os
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Suppress non-breaking ecosystem deprecation notices
warnings.filterwarnings("ignore", message=".*TavilySearchResults.*")
warnings.filterwarnings("ignore", message=".*langchain-community.*")

load_dotenv()

# --------------------------------------------------
# Text Extraction Helper
# --------------------------------------------------

def extract_text(content: Any) -> str:
    """Extract clean string text from LLM response content (supports str and list of parts)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif hasattr(part, "text"):
                text_parts.append(getattr(part, "text", ""))
            else:
                text_parts.append(str(part))
        return "".join(text_parts)
    return str(content)


# --------------------------------------------------
# Search Tools
# --------------------------------------------------

def _create_tavily_tool():
    """Create Tavily search tool with fallback for import safety without keys."""
    api_key = os.getenv("TAVILY_API_KEY")
    try:
        from langchain_tavily import TavilySearch
        if api_key:
            return TavilySearch(max_results=6, tavily_api_key=api_key)
        return TavilySearch(max_results=6, tavily_api_key="tvly-placeholder")
    except Exception:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            if api_key:
                return TavilySearchResults(max_results=6, search_depth="advanced", tavily_api_key=api_key)
            return TavilySearchResults(max_results=6, search_depth="advanced")
        except Exception:
            @tool
            def tavily_search(query: str) -> str:
                """Search the web for information using Tavily."""
                return "Error: Tavily search tool could not be initialized. Please check TAVILY_API_KEY."
            return tavily_search


tavily_search = _create_tavily_tool()

wikipedia = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(
        top_k_results=3,
        doc_content_chars_max=4000
    )
)


@tool
def get_current_date() -> str:
    """Returns today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


# --------------------------------------------------
# File Tools
# --------------------------------------------------

def sanitize_name(name: str, max_len: int = 80) -> str:
    """Sanitize titles and topics for safe filesystem usage."""
    safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name)
    safe = re.sub(r"\s+", "_", safe.strip())
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:max_len] or "unnamed"


def ensure_dirs(title: str) -> Dict[str, Path]:
    """Create research_notes/{title}/ and reports/ folders."""
    base = Path.cwd()
    safe_title = sanitize_name(title)
    notes_dir = base / "research_notes" / safe_title
    reports_dir = base / "reports"

    notes_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    return {
        "notes_dir": notes_dir,
        "reports_dir": reports_dir,
        "report_path": reports_dir / f"{safe_title}.md"
    }


def save_research_note(title: str, topic: str, content: Any) -> str:
    """Save researcher's notes to research_notes/{title}/{topic}.md"""
    paths = ensure_dirs(title)
    safe_topic = sanitize_name(topic, max_len=60)
    file_path = paths["notes_dir"] / f"{safe_topic}.md"

    text_content = extract_text(content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    return str(file_path)


def save_final_report(title: str, content: Any) -> str:
    """Save the final report to reports/{title}.md"""
    paths = ensure_dirs(title)
    text_content = extract_text(content)
    with open(paths["report_path"], "w", encoding="utf-8") as f:
        f.write(text_content)
    return str(paths["report_path"])


def list_notes(title: str) -> List[str]:
    """List all note files for a given research title."""
    paths = ensure_dirs(title)
    return [str(p) for p in paths["notes_dir"].glob("*.md")]
