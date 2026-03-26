"""Report generation."""
import json
from collections import Counter
from pathlib import Path
from rich.console import Console
from .models import Action, ActionType, AgentProfile
console = Console()

PROMPT = """Expert: prediction report from simulation.
QUESTION: {q}
SIM: {nr} rounds, {na} agents, {nact} actions
AGENTS: {agents}
ACTIONS: {actions}
STANCES: {stances}
Write markdown: Executive Summary (confidence %), Key Prediction, Supporting Factors, Risk Factors, Scenario Analysis (3 with %), Key Dynamics, Timeline, Confidence Assessment."""

async def generate_report(question, agents, actions, num_rounds, llm):
    ag = "\n".join(f"- {a.name} ({a.entity_type}): {a.role} | {a.stance} | inf={a.influence_weight}" for a in agents)
    m = [a for a in actions if a.action_type!=ActionType.DO_NOTHING]
    act = "\n".join(f"[R{a.round_num}] {a.agent_name} ({a.action_type.value}): {a.content}" for a in m[-50:])
    st = dict(Counter(a.stance for a in agents))
    with console.status("[bold cyan]Generating report..."):
        report = await llm.complete(PROMPT.format(q=question, nr=num_rounds, na=len(agents), nact=len(m), agents=ag, actions=act, stances=st), temperature=0.4)
    console.print(f"  [green]✓[/green] {len(report)} chars")
    return report

def save_report(report, output_dir):
    p = Path(output_dir)/"report.md"; p.write_text(report)
    console.print(f"  [dim]Saved {p}[/dim]")

def load_actions(output_dir):
    return [Action(**json.loads(l)) for l in (Path(output_dir)/"actions.jsonl").read_text().splitlines() if l.strip()]
