"""Build knowledge graph."""
import json, networkx as nx
from pathlib import Path
from rich.console import Console
from .models import Entity, Relationship, GraphData
from .llm.utils import extract_json
console = Console()

PROMPT = """Analyze text, extract entities and relationships for: {question}

TEXT:
{text}
{enrichment}

Return JSON: {{"entities": [{{"name":"","entity_type":"person|organization|institution|fund|group","description":"","stance":"supportive|opposing|neutral|divided","influence":0.8}}], "relationships": [{{"source":"A","target":"B","relation":"VERB","description":""}}]}}
Extract 8-20 entities, 15-40 relationships."""

async def build_graph(seed_text, question, llm, enrichment_context=""):
    enr = f"\nCONTEXT:\n{enrichment_context}" if enrichment_context else ""
    with console.status("[bold cyan]Extracting entities..."):
        resp = await llm.complete(PROMPT.format(text=seed_text, question=question, enrichment=enr), json_mode=True, temperature=0.3)
    data = extract_json(resp)
    ents = [Entity(**e) for e in data.get("entities",[])]
    rels = [Relationship(**r) for r in data.get("relationships",[])]
    console.print(f"  [green]✓[/green] {len(ents)} entities, {len(rels)} relationships")
    return GraphData(entities=ents, relationships=rels, enrichment_context=enrichment_context)

def save_graph(gd, output_dir):
    p = Path(output_dir)/"graph.json"
    p.write_text(json.dumps(gd.model_dump(), indent=2, ensure_ascii=False))
    console.print(f"  [dim]Saved {p}[/dim]")
