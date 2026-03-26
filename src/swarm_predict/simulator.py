"""Simulation engine."""
import json, random
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from .models import AgentProfile, Action, ActionType
from .llm.utils import extract_json
console = Console()

SYS = """You are {name}. Role: {role} | Objectives: {obj} | Personality: {pers} | Stance: {stance}
Memory: {mem}"""
RND = """Round {r}. Question: {q}
Recent: {recent}
Return JSON: {{"action_type":"post_opinion|respond|support|oppose|change_stance|do_nothing","content":"1-3 sentences","target_agent":"","reasoning":"1 sentence"}}"""

async def run_simulation(agents, question, rounds, llm, output_dir, ratio=0.6):
    all_act = []
    af = Path(output_dir)/"actions.jsonl"
    af.write_text("")
    with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as prog:
        task = prog.add_task("Sim", total=rounds)
        for r in range(1, rounds+1):
            prog.update(task, description=f"Round {r}/{rounds}")
            n = max(2, int(len(agents)*ratio))
            ch = random.choices(agents, weights=[a.activity_level for a in agents], k=min(n,len(agents)))
            seen=set(); active=[a for a in ch if a.name not in seen and not seen.add(a.name)]
            rec = [a for a in all_act if a.round_num>=r-2 and a.action_type!=ActionType.DO_NOTHING]
            rtxt = "\n".join(f"- [{a.agent_name}] {a.action_type.value}: {a.content}" for a in rec[-15:]) or "None."
            prompts = [{"prompt": RND.format(r=r, q=question, recent=rtxt),
                "system": SYS.format(name=ag.name, role=ag.role, obj=", ".join(ag.objectives) if ag.objectives else "Advance interests",
                    pers=ag.personality or "Strategic", stance=ag.stance,
                    mem="\n".join(ag.memory[-10:]) if ag.memory else "None")} for ag in active]
            try: resps = await llm.complete_batch(prompts, json_mode=True, temperature=0.7)
            except Exception as e:
                console.print(f"  [red]R{r} error: {e}[/red]"); prog.advance(task); continue
            ra = []
            for ag, resp in zip(active, resps):
                try:
                    d = extract_json(resp)
                    act = Action(round_num=r, agent_name=ag.name, action_type=ActionType(d.get("action_type","do_nothing")),
                        content=d.get("content",""), target_agent=d.get("target_agent",""), reasoning=d.get("reasoning",""))
                except: act = Action(round_num=r, agent_name=ag.name, action_type=ActionType.DO_NOTHING)
                ra.append(act)
                if act.action_type != ActionType.DO_NOTHING:
                    ag.memory.append(f"[R{r}] I {act.action_type.value}: {act.content}")
                ag.memory = ag.memory[-20:]
            all_act.extend(ra)
            with open(af,"a") as f:
                for a in ra: f.write(json.dumps(a.model_dump(), ensure_ascii=False)+"\n")
            prog.advance(task)
    m = [a for a in all_act if a.action_type!=ActionType.DO_NOTHING]
    console.print(f"  [green]✓[/green] {rounds} rounds: {len(m)} meaningful / {len(all_act)} total")
    return all_act
