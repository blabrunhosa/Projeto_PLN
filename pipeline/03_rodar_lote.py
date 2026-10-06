"""
Rodar lote com retomada

Grava uma linha por item, no formato .jsonl, e sabe retomar de onde parou se a rede cair ou o job for
interrompido.

Uso:
    python 03_rodar_lote.py                  # roda tudo que falta
    python 03_rodar_lote.py --limite 12      # primeiro teste (Padrão 6)
    python 03_rodar_lote.py --comeco 500     # retomar manualmente a partir de um ponto
"""

import argparse
import json
import time

import pandas as pd

from config import CANDIDATOS_CSV, EXTRACOES_JSONL, PAUSA_ENTRE_CHAMADAS_S
from prompt_colisoes import extrair


def ja_processados(caminho) -> set[int]:
    if not caminho.exists():
        return set()
    with caminho.open() as f:
        feitos = {json.loads(l)["i"] for l in f if l.strip()}
    print(f"{len(feitos)} itens já processados -- serão pulados")
    return feitos


def rodar_lote(df: pd.DataFrame, comeco=0, limite=None):
    """Processa df a partir de `comeco`, gravando uma linha por item.

    Cada linha do .jsonl tem o índice `i` (o mesmo índice de candidatos.csv):
    relendo o arquivo você sabe exatamente onde parou, e roda de novo só o
    que falta.
    """
    feitos = ja_processados(EXTRACOES_JSONL)

    alvos = list(df.iloc[comeco:].iterrows())
    if limite:
        alvos = alvos[:limite]

    with EXTRACOES_JSONL.open("a") as f:
        for i, linha in alvos:
            if i in feitos:
                continue
            texto = str(linha["abstract"])
            try:
                registro = {"i": int(i), "entradas": extrair(texto)}
            except Exception as e:  # rede, timeout, cota
                registro = {"i": int(i), "erro": f"{type(e).__name__}: {e}"}
                print(f"  [{i}] falhou: {type(e).__name__}")
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            f.flush()  # o segredo: gravar já, não só no final
            time.sleep(PAUSA_ENTRE_CHAMADAS_S)

    print("fim")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comeco", type=int, default=0)
    ap.add_argument("--limite", type=int, default=None)
    args = ap.parse_args()

    df = pd.read_csv(CANDIDATOS_CSV, index_col="i")
    rodar_lote(df, comeco=args.comeco, limite=args.limite)


if __name__ == "__main__":
    main()
