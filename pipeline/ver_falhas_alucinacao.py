"""
Lista as entradas com confere == False (energia_valor não encontrado no
abstract), lado a lado com o texto de origem, pra inspeção manual.

Uso:
    python ver_falhas_alucinacao.py
"""

import pandas as pd

from config import CANDIDATOS_CSV, EXTRACOES_CHECADAS_CSV

checadas = pd.read_csv(EXTRACOES_CHECADAS_CSV)
candidatos = pd.read_csv(CANDIDATOS_CSV, index_col="i")

falhas = checadas[checadas["confere"] == False]  # noqa: E712

print(f"{len(falhas)} entradas com confere == False\n")

for _, row in falhas.iterrows():
    abstract = candidatos.loc[row["i"], "abstract"]
    print(f"--- i={row['i']} ---")
    print(f"energia_valor extraído: {row['energia_valor']!r} "
          f"{row['energia_unidade']!r} ({row['energia_tipo']!r})")
    print(f"abstract: {abstract}")
    print()
