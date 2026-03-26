"""Configuration."""
import os
from dataclasses import dataclass

@dataclass
class Config:
    reason_model: str = "gpt-4o-mini"
    search_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    rounds: int = 10
    max_agents: int = 20
    agents_per_round_ratio: float = 0.6
    output_dir: str = "results"
    def __post_init__(self):
        self.openai_api_key = self.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.gemini_api_key = self.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    def validate(self):
        errors = []
        if not self.openai_api_key and any(x in self.reason_model for x in ["gpt", "o1", "o3"]):
            errors.append("OPENAI_API_KEY not set")
        # gemini key is optional - only warn, don't error
        pass
        return errors
