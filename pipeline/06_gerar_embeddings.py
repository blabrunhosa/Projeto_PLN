"""
Gera embeddings para retrieval de artigos científicos usando SPECTER2
com o adapter de proximity.

Entrada:
    ../saida/extracoes_agrupadas.jsonl
    candidatos.csv

Saída:
    ../saida/extracoes_embeddings.jsonl

O embedding final possui 768 dimensões e é normalizado
com norma L2 = 1.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer
from adapters import AutoAdapterModel
from config import (
    CANDIDATOS_CSV,
    EXTRACOES_AGRUPADAS_JSONL,
    EXTRACOES_EMBEDDINGS_JSONL,
)

MODELO_BASE = "allenai/specter2_base"
ADAPTER = "allenai/specter2"

TAMANHO_LOTE = 16


def carregar_modelo():
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"dispositivo: {dispositivo}")
    print(f"carregando modelo base: {MODELO_BASE}")

    tokenizer = AutoTokenizer.from_pretrained(MODELO_BASE)

    modelo = AutoAdapterModel.from_pretrained(MODELO_BASE)

    print(f"carregando adapter: {ADAPTER}")

    adapter_name = modelo.load_adapter(
        ADAPTER,
        source="hf",
        load_as="proximity",
        set_active=True,
    )

    modelo.active_adapters = adapter_name

    print(f"adapter carregado: {adapter_name}")
    print(f"adapters disponíveis: {modelo.adapters_config.adapters}")
    print(f"adapter ativo: {modelo.active_adapters}")

    modelo = modelo.to(dispositivo)
    modelo.eval()

    return tokenizer, modelo, dispositivo


def gerar_embeddings(textos: list[str]) -> np.ndarray:
    tokenizer, modelo, dispositivo = carregar_modelo()

    vetores = []

    with torch.no_grad():

        for inicio in range(
            0,
            len(textos),
            TAMANHO_LOTE,
        ):

            lote = textos[
                inicio:inicio + TAMANHO_LOTE
            ]

            entradas = tokenizer(
                lote,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
                return_token_type_ids=False,
            )

            entradas = {
                chave: valor.to(dispositivo)
                for chave, valor in entradas.items()
            }

            saida = modelo(**entradas)

            # Embedding do token [CLS]
            emb = saida.last_hidden_state[:, 0, :]

            # Normalização L2
            emb = torch.nn.functional.normalize(
                emb,
                p=2,
                dim=1,
            )

            emb = emb.cpu().numpy()

            vetores.append(emb)

            fim = min(
                inicio + TAMANHO_LOTE,
                len(textos),
            )

            print(
                f"  {fim}/{len(textos)}"
            )

    return np.concatenate(
        vetores,
        axis=0,
    )


def carregar_extracoes_agrupadas(path: Path) -> dict:
    registros = {}

    with open(
        path,
        encoding="utf-8",
    ) as f:

        for numero_linha, linha in enumerate(
            f,
            start=1,
        ):

            linha = linha.strip()

            if not linha:
                continue

            try:
                registro = json.loads(linha)

            except json.JSONDecodeError as e:
                raise ValueError(
                    f"JSON inválido na linha "
                    f"{numero_linha}: {e}"
                )

            if "i" not in registro:
                raise ValueError(
                    f"Registro na linha "
                    f"{numero_linha} sem campo 'i': "
                    f"{registro}"
                )

            registros[int(registro["i"])] = registro

    return registros


def main():

    # ---------------------------------------------------------
    # 1. Carrega as extrações agrupadas
    # ---------------------------------------------------------

    extracoes = carregar_extracoes_agrupadas(
        EXTRACOES_AGRUPADAS_JSONL
    )

    print(
        f"extrações carregadas: {len(extracoes)}"
    )

    # ---------------------------------------------------------
    # 2. Carrega candidatos.csv
    # ---------------------------------------------------------

    candidatos = pd.read_csv(
        CANDIDATOS_CSV,
        index_col="i",
    )

    print(
        f"candidatos carregados: {len(candidatos)}"
    )

    # ---------------------------------------------------------
    # 3. Verifica os índices
    # ---------------------------------------------------------

    indices = list(extracoes.keys())

    faltando = [
        i
        for i in indices
        if i not in candidatos.index
    ]

    if faltando:
        raise ValueError(
            f"{len(faltando)} índice(s) de "
            f"extracoes_agrupadas não estão em "
            f"candidatos.csv. "
            f"Exemplos: {faltando[:5]}"
        )

    # ---------------------------------------------------------
    # 4. Tokenizer
    # ---------------------------------------------------------

    tokenizer = AutoTokenizer.from_pretrained(
        MODELO_BASE
    )

    # ---------------------------------------------------------
    # 5. Monta título + [SEP] + abstract
    # ---------------------------------------------------------

    textos = []

    for i in indices:

        titulo = candidatos.loc[i, "titulo"]
        abstract = candidatos.loc[i, "abstract"]

        if pd.isna(titulo):
            titulo = ""

        if pd.isna(abstract):
            abstract = ""

        texto = (
            str(titulo)
            + tokenizer.sep_token
            + str(abstract)
        )

        textos.append(texto)

    # ---------------------------------------------------------
    # 6. Gera embeddings
    # ---------------------------------------------------------

    print(
        f"gerando embeddings de "
        f"{len(textos)} artigos..."
    )

    vetores = gerar_embeddings(
        textos
    )

    # ---------------------------------------------------------
    # 7. Verifica dimensão
    # ---------------------------------------------------------

    print(
        f"dimensão dos embeddings: "
        f"{vetores.shape[1]}"
    )

    if vetores.shape[1] != 768:
        raise ValueError(
            f"Dimensão inesperada: "
            f"{vetores.shape[1]}. "
            f"Esperado: 768."
        )

    # ---------------------------------------------------------
    # 8. Verifica normalização
    # ---------------------------------------------------------

    normas = np.linalg.norm(
        vetores,
        axis=1,
    )

    print(
        f"norma mínima: {normas.min():.6f}"
    )

    print(
        f"norma máxima: {normas.max():.6f}"
    )

    if not np.allclose(
        normas,
        1.0,
        atol=1e-5,
    ):
        raise ValueError(
            "Os embeddings não estão "
            "normalizados corretamente."
        )

    # ---------------------------------------------------------
    # 9. Monta saída
    # ---------------------------------------------------------

    saida = []

    for i, vetor in zip(
        indices,
        vetores,
    ):

        registro = dict(
            extracoes[i]
        )

        registro["i"] = i
        registro["embedding"] = vetor.tolist()

        saida.append(registro)

    # ---------------------------------------------------------
    # 10. Salva JSONL
    # ---------------------------------------------------------

    EXTRACOES_EMBEDDINGS_JSONL.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        EXTRACOES_EMBEDDINGS_JSONL,
        "w",
        encoding="utf-8",
    ) as f:

        for registro in saida:

            f.write(
                json.dumps(
                    registro,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"salvo em: "
        f"{EXTRACOES_EMBEDDINGS_JSONL}"
    )


if __name__ == "__main__":
    main()