"""Pydantic models."""
from pydantic import BaseModel, Field
from enum import Enum

class Entity(BaseModel):
    name: str
    entity_type: str
    description: str
    stance: str = ""
    influence: float = Field(default=0.5, ge=0.0, le=1.0)

class Relationship(BaseModel):
    source: str
    target: str
    relation: str
    description: str = ""

class GraphData(BaseModel):
    entities: list[Entity] = []
    relationships: list[Relationship] = []
    enrichment_context: str = ""

class AgentProfile(BaseModel):
    agent_id: int = 0
    name: str
    entity_type: str = ""
    role: str = ""
    objectives: list[str] = []
    personality: str = ""
    stance: str = "neutral"
    influence_weight: float = 1.0
    activity_level: float = Field(default=0.5, ge=0.0, le=1.0)
    initial_knowledge: str = ""
    memory: list[str] = []

class ActionType(str, Enum):
    POST_OPINION = "post_opinion"
    RESPOND = "respond"
    SUPPORT = "support"
    OPPOSE = "oppose"
    CHANGE_STANCE = "change_stance"
    DO_NOTHING = "do_nothing"

class Action(BaseModel):
    round_num: int
    agent_name: str
    action_type: ActionType
    content: str = ""
    target_agent: str = ""
    reasoning: str = ""

class SimulationState(BaseModel):
    simulation_id: str
    seed_file: str
    question: str
    graph: GraphData = Field(default_factory=GraphData)
    agents: list[AgentProfile] = []
    total_rounds: int = 10
    current_round: int = 0
    status: str = "created"
    report: str = ""
