"""
Lista os observáveis de um .jsonl de extrações e quantas vezes cada um aparece.

Uso:
    python contar_observaveis.py extracoes_tratadas.jsonl
    python contar_observaveis.py extracoes_tratadas.jsonl --csv outro/caminho.csv   # opcional
"""
import argparse
import csv
import json
import os
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo", help="caminho do .jsonl")
    ap.add_argument("--csv", default="../saida/observaveis.csv",
                    help="caminho do CSV de saída (padrão: ../saida/observaveis.csv)")
    args = ap.parse_args()

    por_entrada = Counter()   # cada entrada (medição) conta 1 vez por observável
    por_artigo = Counter()    # cada artigo (campo "i") conta 1 vez por observável
    n_artigos = n_entradas = 0

    with open(args.arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            reg = json.loads(linha)
            n_artigos += 1
            vistos = set()
            for e in reg.get("entradas", []):
                n_entradas += 1
                obs = set(e.get("observaveis") or [])  # set: evita contar repetido na mesma entrada
                por_entrada.update(obs)
                vistos |= obs
            por_artigo.update(vistos)

    print(f"Artigos: {n_artigos} | Entradas: {n_entradas} | Observáveis distintos: {len(por_entrada)}\n")
    w = max(len(k) for k in por_entrada)
    print(f"{'observável':<{w}}  {'entradas':>8}  {'artigos':>8}")
    print("-" * (w + 20))
    linhas = []
    for obs, n in por_entrada.most_common():
        print(f"{obs:<{w}}  {n:>8}  {por_artigo[obs]:>8}")
        linhas.append((obs, n, por_artigo[obs]))

    os.makedirs(os.path.dirname(os.path.abspath(args.csv)), exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["observavel", "entradas", "artigos"])
        wr.writerows(linhas)
    print(f"\nSalvo em {args.csv}")


if __name__ == "__main__":
    main()
