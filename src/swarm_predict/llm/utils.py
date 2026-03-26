"""JSON extraction."""
import json, re

def extract_json(text):
    text = text.strip()
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    for pat in [r"```json\s*\n?(.*?)\n?```", r"```\s*\n?(.*?)\n?```"]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            try: return json.loads(m.group(1))
            except: continue
    for pat in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        m = re.search(pat, text)
        if m:
            try: return json.loads(m.group(0))
            except: continue
    raise ValueError(f"No JSON: {text[:200]}")
