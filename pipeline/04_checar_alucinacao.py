"""
Detectar alucinação.

Um regex nunca devolve um número que não está no texto. Um modelo pode e devolve com a mesma confiança do acerto. A checagem mais barata que
existe: o valor extraído aparece no texto de origem?

Lê ../saida/extracoes_agrupadas.jsonl (uma linha por resumo, com o campo
'entradas' contendo as extrações daquele resumo.
"""

import json
import re

import pandas as pd

from config import CANDIDATOS_CSV, EXTRACOES_CHECADAS_CSV, EXTRACOES_AGRUPADAS_JSONL


def normaliza_numeros(texto: str) -> str:
    """Corrige artefatos comuns de OCR/extração de PDF em números, pra não
    gerar falso negativo na checagem de alucinação. Vistos na prática:
      - parênteses em volta de parte da mantissa: "(12).3" -> "12.3"
      - dois-pontos usado no lugar do ponto decimal: "5:02" -> "5.02"
      - espaços em volta do ponto decimal: "2 . 76" -> "2.76"
    """
    t = texto
    t = re.sub(r"\((\d+)\)\.(\d+)", r"\1.\2", t)
    t = re.sub(r"(\d):(\d)", r"\1.\2", t)
    t = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", t)
    return t


def formas_de_range(v: str) -> set[str]:
    """Pra valores tipo "90-365" (faixa), gera as formas alternativas que o
    texto original costuma usar por extenso ("90 and 365", "90 to 365")."""
    m = re.match(r"^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$", v)
    if not m:
        return set()
    a, b = m.group(1), m.group(2)
    return {f"{a}-{b}", f"{a} and {b}", f"{a} to {b}", f"{a}, {b}"}


def confere_no_texto(entradas: list[dict], origem: str) -> list[dict]:
    """Marca cada entrada conforme o valor de energia apareça, ou não, no
    texto original. Checa tanto o texto como veio quanto uma versão
    normalizada (ver normaliza_numeros), pra não penalizar o modelo por
    artefatos de OCR/extração que não são culpa dele."""
    origem_norm = normaliza_numeros(origem)

    for e in entradas:
        v = e.get("energia_valor")
        if v is None:
            e["confere"] = None
            continue

        if isinstance(v, str):
            # o LLM às vezes devolve string em vez de número puro
            # (ex.: "11.6A", "90-365", "200A")
            formas = {v} | formas_de_range(v)
            e["confere"] = any(f in origem or f in origem_norm for f in formas)
            continue

        # aceita a forma com e sem casas decimais (200 vs 200.0)
        formas = {f"{v:g}", str(v)}
        e["confere"] = any(f in origem or f in origem_norm for f in formas)
    return entradas


def main():
    candidatos = pd.read_csv(CANDIDATOS_CSV, index_col="i")

    linhas = []
    with EXTRACOES_AGRUPADAS_JSONL.open(encoding="utf-8") as f:
        for l in f:
            if not l.strip():
                continue
            d = json.loads(l)
            origem = str(candidatos.loc[d["i"], "abstract"])
            for e in confere_no_texto(d["entradas"], origem):
                linhas.append({"i": d["i"], **e})

    df = pd.DataFrame(linhas)
    df.to_csv(EXTRACOES_CHECADAS_CSV, index=False, encoding="utf-8-sig")

    total = len(df)
    if total == 0:
        print("nenhuma entrada encontrada em extracoes_agrupadas.jsonl")
        return

    com_valor = df["confere"].notna().sum()
    ok = (df["confere"] == True).sum()  # noqa: E712
    print(f"{total} entradas no total")
    print(f"{com_valor} tinham energia_valor preenchido")
    print(f"{ok} conferem no texto original ({ok / com_valor:.1%} das que "
          f"tinham valor)" if com_valor else "nenhuma tinha valor pra checar")
    print(f"salvo em: {EXTRACOES_CHECADAS_CSV}")


if __name__ == "__main__":
    main()