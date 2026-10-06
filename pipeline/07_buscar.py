"""
Busca semântica nos abstracts candidatos via similaridade de cosseno.

- Documentos de entrada: embeddings já gerados em ../saida/extracoes_embeddings.jsonl
  (SPECTER2 com o adapter de proximity, normalizados com norma L2 = 1).

- Query: vetorizada aqui com o adapter allenai/specter2_adhoc_query, que é o
  recomendado pelo SPECTER2 para consultas curtas de busca ad-hoc
  (query com adhoc_query, candidatos com proximity).

Como os dois lados são normalizados (norma 1), o cosseno é só o produto
escalar.

Uso:
    python 07_buscar.py                       # modo interativo
    python 07_buscar.py -q "quark gluon plasma elliptic flow" -k 5
    python 07_buscar.py -k 20 --completo      # abstracts sem truncar
"""

import argparse
import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from adapters import AutoAdapterModel
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

from config import (
    CANDIDATOS_CSV, 
    EXTRACOES_EMBEDDINGS_JSONL
    )

PASTA_ADAPTER_LOCAL = Path(__file__).resolve().parent / "../specter/specter2_adhoc_query"

MODELO_BASE = "allenai/specter2_base"
ADAPTER_QUERY = "allenai/specter2_adhoc_query"


def carregar_indice(path: Path) -> tuple[list[int], np.ndarray]:
    """Lê o jsonl e devolve (lista de i, matriz N x 768 float32)."""
    indices, vetores = [], []
    with open(path, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            registro = json.loads(linha)
            indices.append(int(registro["i"]))
            vetores.append(registro["embedding"])

    matriz = np.asarray(vetores, dtype=np.float32)

    # garante norma 1 (já deveria ser, mas custa nada)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    matriz = matriz / np.clip(normas, 1e-12, None)
    return indices, matriz


def carregar_modelo_query():
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"dispositivo: {dispositivo}")

    tokenizer = AutoTokenizer.from_pretrained(MODELO_BASE)
    modelo = AutoAdapterModel.from_pretrained(MODELO_BASE)

    # Baixa o adapter direto pra uma pasta local (arquivos reais, sem
    # symlinks). O cache padrão do HF usa symlinks, que no Windows falham
    # com WinError 1314 se o Modo Desenvolvedor não estiver ativo.
    # Depois do primeiro download, isso também funciona offline.
    pasta_adapter = snapshot_download(
        ADAPTER_QUERY, local_dir=PASTA_ADAPTER_LOCAL
    )
    nome = modelo.load_adapter(
        pasta_adapter, load_as="adhoc_query", set_active=True
    )
    modelo.active_adapters = nome
    print(f"adapter ativo: {modelo.active_adapters}")

    modelo = modelo.to(dispositivo).eval()
    return tokenizer, modelo, dispositivo


def embedar_query(query: str, tokenizer, modelo, dispositivo) -> np.ndarray:
    entradas = tokenizer(
        [query],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
        return_token_type_ids=False,
    )
    entradas = {k: v.to(dispositivo) for k, v in entradas.items()}

    with torch.no_grad():
        saida = modelo(**entradas)
        emb = saida.last_hidden_state[:, 0, :]  # token [CLS]
        emb = torch.nn.functional.normalize(emb, p=2, dim=1)

    return emb.cpu().numpy()[0]


def buscar(vetor_query: np.ndarray, matriz: np.ndarray, k: int):
    """Devolve (posições, scores) dos k mais similares, do maior pro menor."""
    scores = matriz @ vetor_query
    k = min(k, len(scores))
    topo = np.argpartition(-scores, k - 1)[:k]
    topo = topo[np.argsort(-scores[topo])]
    return topo, scores[topo]


def mostrar_resultados(topo, scores, indices, candidatos, completo: bool):
    for rank, (pos, score) in enumerate(zip(topo, scores), start=1):
        i = indices[pos]
        linha = candidatos.loc[i]

        titulo = linha["titulo"] if pd.notna(linha["titulo"]) else "(sem título)"
        ano = linha["ano"] if pd.notna(linha["ano"]) else "?"
        abstract = linha["abstract"] if pd.notna(linha["abstract"]) else ""

        if not completo and len(abstract) > 500:
            abstract = abstract[:500].rstrip() + "..."

        print(f"\n[{rank}] cosseno={score:.4f}  i={i}  ano={ano}")
        print(f"    {titulo}")
        if abstract:
            print(textwrap.fill(
                abstract, width=100,
                initial_indent="    ", subsequent_indent="    ",
            ))


def main():
    parser = argparse.ArgumentParser(description="Busca semântica nos abstracts")
    parser.add_argument("-q", "--query", help="query única (sem modo interativo)")
    parser.add_argument("-k", type=int, default=10, help="quantos resultados (padrão 10)")
    parser.add_argument("--completo", action="store_true", help="não truncar abstracts")
    args = parser.parse_args()

    print("carregando embeddings...")
    indices, matriz = carregar_indice(EXTRACOES_EMBEDDINGS_JSONL)
    print(f"  {len(indices)} documentos, dimensão {matriz.shape[1]}")

    candidatos = pd.read_csv(CANDIDATOS_CSV, index_col="i")

    print("carregando modelo de query...")
    tokenizer, modelo, dispositivo = carregar_modelo_query()

    def rodar(query: str):
        vetor = embedar_query(query, tokenizer, modelo, dispositivo)
        topo, scores = buscar(vetor, matriz, args.k)
        mostrar_resultados(topo, scores, indices, candidatos, args.completo)

    if args.query:
        rodar(args.query)
        return

    print("\npronto. Digite uma query (vazio ou 'sair' pra encerrar).")
    while True:
        try:
            query = input("\nquery> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query or query.lower() in {"sair", "exit", "quit"}:
            break
        rodar(query)


if __name__ == "__main__":
    main()
