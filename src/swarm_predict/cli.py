"""CLI."""
import asyncio, json, sys, uuid
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .config import Config
from .models import SimulationState, AgentProfile
console = Console()

def run_async(coro): return asyncio.run(coro)

def create_llm(api_key, model):
    if "gemini" in model.lower():
        from .llm.gemini_llm import GeminiProvider
        return GeminiProvider(api_key=api_key, model=model)
    from .llm.openai_llm import OpenAIProvider
    return OpenAIProvider(api_key=api_key, model=model)

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """swarm-predict: Multi-agent prediction engine."""

@cli.command()
@click.option("--seed", required=True, type=click.Path(exists=True))
@click.option("--question", required=True)
@click.option("--rounds", default=10)
@click.option("--reason-model", default="gpt-4o-mini")
@click.option("--search-model", default="gemini-2.0-flash")
@click.option("--output", default="results")
@click.option("--no-enrich", is_flag=True)
@click.option("--max-agents", default=15)
def run(seed, question, rounds, reason_model, search_model, output, no_enrich, max_agents):
    """Run prediction simulation."""
    run_async(_run(seed, question, rounds, reason_model, search_model, output, no_enrich, max_agents))

async def _run(seed, question, rounds, reason_model, search_model, output, no_enrich, max_agents):
    from .graph_builder import build_graph, save_graph
    from .enricher import enrich_with_search
    from .agent_generator import generate_agents
    from .simulator import run_simulation
    from .reporter import generate_report, save_report
    cfg = Config(reason_model=reason_model, search_model=search_model, rounds=rounds, max_agents=max_agents)
    errs = cfg.validate()
    if errs:
        for e in errs: console.print(f"[red]{e}[/red]")
        sys.exit(1)
    sid = f"sim_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:6]}"
    out = Path(output)/sid; out.mkdir(parents=True, exist_ok=True)
    console.print(Panel(f"Q: {question}\nSeed: {seed}\nRounds: {rounds}\nReason: {reason_model}\nOutput: {out}", title="swarm-predict", border_style="cyan"))
    stxt = Path(seed).read_text()
    rllm = create_llm(cfg.openai_api_key, reason_model)
    enr = ""
    if not no_enrich and cfg.gemini_api_key:
        sllm = create_llm(cfg.gemini_api_key, search_model)
        enr = await enrich_with_search(stxt, question, sllm); await sllm.close()
    elif not no_enrich: console.print("  [yellow]No GEMINI_API_KEY, skip enrich[/yellow]")
    console.print("\n[bold]Phase 1: Graph[/bold]")
    gd = await build_graph(stxt, question, rllm, enr); save_graph(gd, out)
    console.print("\n[bold]Phase 2: Agents[/bold]")
    ags = await generate_agents(gd, question, rllm, max_agents)
    (out/"agents.json").write_text(json.dumps([a.model_dump() for a in ags], indent=2, ensure_ascii=False))
    t = Table(title="Agents"); t.add_column("Name",style="bold"); t.add_column("Stance"); t.add_column("Influence")
    for a in ags:
        c={"supportive":"green","opposing":"red","neutral":"yellow","divided":"magenta"}.get(a.stance,"white")
        t.add_row(a.name, f"[{c}]{a.stance}[/{c}]", f"{a.influence_weight:.1f}")
    console.print(t)
    console.print(f"\n[bold]Phase 3: Simulate ({rounds} rounds)[/bold]")
    acts = await run_simulation(ags, question, rounds, rllm, out, cfg.agents_per_round_ratio)
    console.print("\n[bold]Phase 4: Report[/bold]")
    rep = await generate_report(question, ags, acts, rounds, rllm); save_report(rep, out)
    st = SimulationState(simulation_id=sid, seed_file=str(seed), question=question, graph=gd, agents=ags,
        total_rounds=rounds, current_round=rounds, status="completed", report=str(out/"report.md"))
    (out/"state.json").write_text(json.dumps(st.model_dump(), indent=2, ensure_ascii=False, default=str))
    await rllm.close()
    console.print(Panel(rep[:2000]+("..." if len(rep)>2000 else ""), title="Report", border_style="green"))
    console.print(f"\n[green]✓ Done![/green] {out}/")

@cli.command()
@click.option("--simulation", required=True, type=click.Path(exists=True))
def agents(simulation):
    """List agents."""
    d = json.loads((Path(simulation)/"agents.json").read_text())
    t = Table(title="Agents"); t.add_column("Name"); t.add_column("Stance"); t.add_column("Role")
    for a in d: t.add_row(a["name"], a.get("stance",""), a.get("role","")[:60])
    console.print(t)

if __name__ == "__main__": cli()
