"""
Deep Research Agent - Main Entry Point
Coordinator → Parallel Specialized Researchers → Report Writer
"""

import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from agents.coordinator import Coordinator
from agents.researcher import Researcher
from agents.report_writer import ReportWriter
from tools.research_tools import ensure_dirs

load_dotenv()
console = Console()


def run_deep_research(question: str, clarifications: str = "", model: str = None):
    console.print(Panel(f"[bold cyan]Deep Research Started[/bold cyan]\n\n{question}", title="Query"))

    # -------------------------------------------------------
    # 1. Coordinator - Plan the research
    # -------------------------------------------------------
    console.print("\n[bold yellow]→ Coordinator is planning...[/bold yellow]")
    coordinator = Coordinator(model=model)
    plan = coordinator.plan(question, clarifications)

    if plan.get("needs_clarification") and plan.get("questions"):
        console.print("\n[bold red]Clarification needed:[/bold red]")
        for q in plan["questions"]:
            console.print(f"  • {q}")
        return None

    title = plan.get("title", "Research Report")
    subtopics = plan.get("subtopics", [])

    console.print(f"\n[green]Research Title:[/green] {title}")
    console.print(f"[green]Subtopics ({len(subtopics)}):[/green]")
    for i, sub in enumerate(subtopics, 1):
        console.print(f"  {i}. {sub['topic']}")

    # Create folders
    paths = ensure_dirs(title)

    # -------------------------------------------------------
    # 2. Parallel Researchers
    # -------------------------------------------------------
    console.print("\n[bold yellow]→ Starting parallel research...[/bold yellow]")

    researcher = Researcher(model=model)
    notes = {}

    def run_one_researcher(subtopic):
        topic_name = subtopic["topic"]
        console.print(f"  [cyan]Researching:[/cyan] {topic_name}")
        result = researcher.research(title, subtopic)
        return topic_name, result

    # Run researchers in parallel
    max_workers = int(os.getenv("DR_MAX_RESEARCHERS", 3))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_one_researcher, sub) for sub in subtopics]

        for future in as_completed(futures):
            try:
                topic_name, result = future.result()
                notes[topic_name] = result
            except Exception as e:
                console.print(f"[red]Researcher failed for subtopic: {e}[/red]")

    if not notes:
        console.print("[bold red]All researchers failed. Exiting.[/bold red]")
        return None

    console.print(f"\n[green]✓ All research notes collected ({len(notes)})[/green]")

    # -------------------------------------------------------
    # 3. Report Writer
    # -------------------------------------------------------
    console.print("\n[bold yellow]→ Writing final report...[/bold yellow]")
    writer = ReportWriter(model=model)
    final_report = writer.write_report(question, title, notes)

    # -------------------------------------------------------
    # 4. Done
    # -------------------------------------------------------
    console.print(Panel(
        f"[bold green]Research Complete![/bold green]\n\n"
        f"Title: {title}\n"
        f"Notes saved in: {paths['notes_dir']}\n"
        f"Final report: {paths['report_path']}",
        title="Finished"
    ))

    return final_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deep Research Agents: Autonomous Multi-Agent Research System"
    )
    parser.add_argument("query", nargs="*", help="Research question or topic")
    parser.add_argument("--clarifications", "-c", default="", help="Optional clarification context")
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Model override (e.g., nvidia/nemotron-3-ultra-550b-a55b:free, gemini-3.5-flash)"
    )

    args = parser.parse_args()

    if args.query:
        query = " ".join(args.query).strip()
    else:
        query = input("\nEnter your research question: ").strip()

    if not query:
        console.print("[red]No question provided.[/red]")
        sys.exit(1)

    run_deep_research(query, clarifications=args.clarifications, model=args.model)
