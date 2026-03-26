"""Gemini provider with grounding."""
import asyncio, httpx
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, api_key, model="gemini-2.0-flash", grounding=True):
        self.api_key, self.model, self.grounding = api_key, model, grounding
        self._client = None
    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client
    async def complete(self, prompt, system="", json_mode=False, temperature=0.7):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature}}
        if system: body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode: body["generationConfig"]["responseMimeType"] = "application/json"
        if self.grounding: body["tools"] = [{"google_search": {}}]
        r = await self.client.post(url, json=body)
        r.raise_for_status()
        d = r.json()
        try: return "\n".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"] if "text" in p)
        except: return ""
    async def complete_batch(self, prompts, json_mode=False, temperature=0.7):
        sem = asyncio.Semaphore(5)
        async def _c(p):
            async with sem: return await self.complete(p["prompt"], p.get("system",""), json_mode, temperature)
        return await asyncio.gather(*[_c(p) for p in prompts])
    async def close(self):
        if self._client and not self._client.is_closed: await self._client.aclose()
