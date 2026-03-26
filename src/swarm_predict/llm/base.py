"""Abstract LLM provider."""
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt, system="", json_mode=False, temperature=0.7): ...
    @abstractmethod
    async def complete_batch(self, prompts, json_mode=False, temperature=0.7): ...
