"""Gemini grounding enrichment."""
from rich.console import Console
console = Console()

async def enrich_with_search(seed_text, question, search_llm):
    prompt = f"Research recent context for: {question}\n\nScenario: {seed_text}\n\nProvide factual recent events, positions, dynamics."
    with console.status("[bold cyan]Enriching with web search..."):
        try:
            r = await search_llm.complete(prompt, temperature=0.3)
            if r.strip():
                console.print(f"  [green]✓[/green] {len(r)} chars")
                return r
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Failed: {e}")
    return ""
