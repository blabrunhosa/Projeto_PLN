"""
Calculo de precisao: mostra um abstract por vez (com a extracao feita pra
ele), voce responde se esta certo ou nao, e no final sai a precisao.

Precisa de DOIS arquivos (caminhos vem do config.py):
  - candidatos.csv           -> tem o texto do abstract (colunas: i, abstract, ...)
  - extracoes_agrupadas.jsonl -> tem as extracoes (colunas: i, entradas)
Junta os dois pelo 'i'.
"""

import json
import csv
import random
from pathlib import Path

from config import CANDIDATOS_CSV, EXTRACOES_AGRUPADAS_JSONL

# o config nao tem um caminho pro arquivo de revisao, entao ele fica na mesma
# pasta (saida/) das extracoes. Se preferir, crie REVISAO_JSONL no config.py.
REVISAO_JSONL = EXTRACOES_AGRUPADAS_JSONL.parent / "revisao.jsonl"

RESPOSTAS_VALIDAS = {
    "s": "s", "sim": "s",
    "n": "n", "nao": "n", "não": "n",
    "p": "p", "pular": "p",
    "q": "q", "sair": "q",
}


def carregar_abstracts(caminho_csv=CANDIDATOS_CSV):
    """dict: i -> texto do abstract"""
    abstracts = {}
    with open(caminho_csv, encoding="utf-8-sig") as f:
        for n_linha, linha in enumerate(csv.DictReader(f), start=2):
            bruto = (linha.get("i") or "").strip()
            if not bruto:
                continue  # linha sem 'i', ignora
            try:
                i = int(bruto)
            except ValueError:
                print(f"[aviso] linha {n_linha} do CSV tem 'i' invalido ({bruto!r}), ignorando.")
                continue
            abstracts[i] = linha.get("abstract", "")
    return abstracts


def carregar_extracoes(caminho_jsonl=EXTRACOES_AGRUPADAS_JSONL):
    """lista de {i, entradas}"""
    extracoes = []
    with open(caminho_jsonl, encoding="utf-8") as f:
        for n_linha, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError as e:
                print(f"[aviso] linha {n_linha} de {caminho_jsonl} nao e JSON valido, ignorando ({e}).")
                continue
            if "i" not in registro or "entradas" not in registro:
                print(f"[aviso] linha {n_linha} de {caminho_jsonl} sem 'i' ou 'entradas', ignorando.")
                continue
            extracoes.append(registro)
    return extracoes


def perguntar(prompt):
    """Repergunta ate receber uma resposta valida (s/n/p/q, aceita por extenso)."""
    while True:
        bruto = input(prompt).strip().lower()
        if bruto in RESPOSTAS_VALIDAS:
            return RESPOSTAS_VALIDAS[bruto]
        print("  (nao entendi -- digite s, n, p ou q)")


def revisar(
    caminho_csv=CANDIDATOS_CSV,
    caminho_jsonl=EXTRACOES_AGRUPADAS_JSONL,
    caminho_revisao=REVISAO_JSONL,
    n=30,
    semente=42,
):
    abstracts = carregar_abstracts(caminho_csv)
    extracoes = carregar_extracoes(caminho_jsonl)

    # ja revisados (por abstract inteiro) -- pra poder parar e continuar depois
    ja_feitos = set()
    caminho_saida = Path(caminho_revisao)
    if caminho_saida.exists():
        with open(caminho_saida, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    d = json.loads(l)
                    ja_feitos.add(d["i"])

    random.seed(semente)
    extracoes_embaralhadas = extracoes[:]
    random.shuffle(extracoes_embaralhadas)

    mostrados = 0
    try:
        with open(caminho_saida, "a", encoding="utf-8") as f_saida:
            for linha in extracoes_embaralhadas:
                if mostrados >= n:
                    break

                i = linha["i"]
                if i in ja_feitos:
                    continue

                abstract = abstracts.get(i)
                if not abstract:
                    continue  # sem texto pra mostrar, pula

                entradas = linha["entradas"]
                if not entradas:
                    continue  # nada extraido pra esse abstract, pula

                print("\n" + "=" * 80)
                print(f"[i={i}]  ({mostrados + 1}/{n})")
                print("-" * 80)
                print(abstract)
                print("-" * 80)
                print("\nExtracoes:")
                for entrada in entradas:
                    print(f"  - {entrada}")

                resposta = perguntar("\nEsta tudo certo? [s=sim / n=nao / p=pular / q=sair] ")

                if resposta == "q":
                    print("Saindo. Progresso salvo.")
                    return
                if resposta == "p":
                    continue

                f_saida.write(json.dumps({
                    "i": i,
                    "correto": resposta == "s",
                }, ensure_ascii=False) + "\n")
                f_saida.flush()
                mostrados += 1
    except KeyboardInterrupt:
        print("\nInterrompido. Progresso ja salvo ate a ultima resposta.")
        return

    print(f"\n{mostrados} abstracts revisados nesta rodada.")


def calcular_precisao(caminho_revisao=REVISAO_JSONL):
    registros = []
    with open(caminho_revisao, encoding="utf-8") as f:
        for l in f:
            if l.strip():
                registros.append(json.loads(l))

    if not registros:
        print("Nenhum julgamento ainda.")
        return None

    corretos = sum(1 for r in registros if r["correto"])
    total = len(registros)
    precisao = corretos / total

    print(f"Total julgado: {total}")
    print(f"Corretos: {corretos}")
    print(f"Precisao: {precisao:.1%}")
    return precisao


if __name__ == "__main__":
    revisar(n=30)
    calcular_precisao()