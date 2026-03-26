"""OpenAI provider."""
import asyncio, httpx
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model="gpt-4o-mini", base_url="https://api.openai.com/v1"):
        self.api_key, self.model, self.base_url = api_key, model, base_url
        self._client = None
    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=120.0)
        return self._client
    async def complete(self, prompt, system="", json_mode=False, temperature=0.7):
        msgs = []
        if system: msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        body = {"model": self.model, "messages": msgs, "temperature": temperature}
        if json_mode: body["response_format"] = {"type": "json_object"}
        r = await self.client.post("/chat/completions", json=body)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    async def complete_batch(self, prompts, json_mode=False, temperature=0.7):
        sem = asyncio.Semaphore(10)
        async def _c(p):
            async with sem: return await self.complete(p["prompt"], p.get("system",""), json_mode, temperature)
        return await asyncio.gather(*[_c(p) for p in prompts])
    async def close(self):
        if self._client and not self._client.is_closed: await self._client.aclose()
