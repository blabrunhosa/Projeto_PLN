"""
JSON que não quebra o laço.
"""

import json
import re


def ler_json(texto: str) -> dict:
    """Tolera cercas de markdown e texto solto em volta do JSON."""
    t = texto.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        # última tentativa: o maior trecho entre chaves
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    print("  (resposta não era JSON):", t[:120])
    return {}
