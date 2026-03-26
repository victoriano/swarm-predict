"""Generate agents from graph."""
from rich.console import Console
from .models import GraphData, AgentProfile
from .llm.utils import extract_json
console = Console()

PROMPT = """Agent profile for: {name} ({etype})
Desc: {desc} | Stance: {stance} | Influence: {inf}
Rels: {rels}
Question: {q}
Return JSON: {{"name":"{name}","role":"","objectives":["","",""],"personality":"","stance":"{stance}","influence_weight":{inf},"activity_level":0.5,"initial_knowledge":""}}"""

async def generate_agents(graph, question, llm, max_agents=15):
    ents = sorted(graph.entities, key=lambda e: e.influence, reverse=True)[:max_agents]
    rm = {}
    for r in graph.relationships:
        rm.setdefault(r.source,[]).append(f"->{r.relation}->{r.target}")
        rm.setdefault(r.target,[]).append(f"<-{r.relation}<-{r.source}")
    prompts = [{"prompt": PROMPT.format(name=e.name, etype=e.entity_type, desc=e.description, stance=e.stance,
        inf=e.influence, rels="; ".join(rm.get(e.name,["None"])), q=question),
        "system": "Return valid JSON only."} for e in ents]
    console.print(f"  Generating {len(prompts)} profiles...")
    resps = await llm.complete_batch(prompts, json_mode=True, temperature=0.4)
    agents = []
    for i, resp in enumerate(resps):
        try:
            d = extract_json(resp)
            agents.append(AgentProfile(agent_id=i, entity_type=ents[i].entity_type, **d))
        except Exception as ex:
            console.print(f"  [yellow]⚠[/yellow] {ents[i].name}: {ex}")
            agents.append(AgentProfile(agent_id=i, name=ents[i].name, entity_type=ents[i].entity_type,
                role=ents[i].description, stance=ents[i].stance, influence_weight=ents[i].influence))
    console.print(f"  [green]✓[/green] {len(agents)} agents")
    return agents
