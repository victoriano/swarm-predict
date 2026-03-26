"""Agent interview."""
from rich.console import Console, Panel
from rich.prompt import Prompt
from .models import AgentProfile, Action, ActionType
console = Console()

async def interview_agent(agent, actions, llm):
    aa = [a for a in actions if a.agent_name==agent.name and a.action_type!=ActionType.DO_NOTHING]
    hist = "\n".join(f"- R{a.round_num}: {a.action_type.value} - {a.content}" for a in aa) or "None."
    sys = f"You are {agent.name}. Role: {agent.role}. Stance: {agent.stance}. Actions: {hist}\nStay in character."
    console.print(f"[bold]{agent.name}[/bold] ({agent.role}). Type quit to end.\n")
    conv = []
    while True:
        q = Prompt.ask("[cyan]You[/cyan]")
        if q.lower() in ("quit","exit","q"): break
        conv.append(f"Q: {q}")
        r = await llm.complete("\n".join(conv)+f"\n{agent.name}:", system=sys, temperature=0.6)
        conv.append(f"{agent.name}: {r}")
        console.print(f"[green]{agent.name}[/green]: {r}\n")
