"""
Filtragem com o regex antes de passar para a LLM

Filtro generoso adotado:
    candidato = colisao_valida OR colisao_duvidosa OR energia OR acelerador OR detector OR instituicao

Saída: ../saida/candidatos.csv, com uma linha por abstract candidato e um índice estável `i`
"""

import pandas as pd

from config import CAMINHOS_XLS, CANDIDATOS_CSV
from regexando import processar_todos_os_arquivos

def marcar_origem(r: dict) -> list[str]:
    """De quais peneiras esse abstract veio, útil pra auditoria depois."""
    origem = []
    if r.get("colisoes"):
        origem.append("colisao_valida")
    if r.get("colisoes_duvidosas"):
        origem.append("colisao_duvidosa")
    if r.get("energia"):
        origem.append("energia")
    if r.get("aceleradores"):
        origem.append("acelerador")
    if r.get("detectores"):
        origem.append("detector")
    if r.get("instituicoes"):
        origem.append("instituicao")
    return origem


def main():
    resultados = processar_todos_os_arquivos([str(p) for p in CAMINHOS_XLS])

    linhas = []
    for r in resultados:
        origem = marcar_origem(r)
        if not origem:
            continue
        linhas.append({
            "arquivo": r["arquivo"],
            "linha_original": r["linha"],
            "titulo": r["titulo"],
            "ano": r["ano"],
            "abstract": r["abstract"],
            "origem_regex": ";".join(origem),
        })

    df = pd.DataFrame(linhas)
    df.index.name = "i"
    
    df.to_csv(CANDIDATOS_CSV, encoding="utf-8-sig")

    total = len(resultados)
    print(f"{total} abstracts processados -> {len(df)} candidatos "
          f"({len(df) / total:.1%})")
    print(f"salvo em: {CANDIDATOS_CSV}")


if __name__ == "__main__":
    main()