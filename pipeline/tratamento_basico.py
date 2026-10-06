"""
Tratamento básico das extrações do LLM: ordena, remove entradas vazias
e anexa o ano de publicação.

Três passos, nessa ordem:

  1. Ordena as linhas de EXTRACOES_JSONL pelo campo `i` (o arquivo como
     sai do pipeline de extração não vem garantidamente ordenado --
     por exemplo em execuções paralelas/em lote os resultados podem
     voltar fora de ordem).

  2. Descarta as linhas em que `entradas` veio vazia (ex.:
     {"i": 5315, "entradas": []}), ou seja, abstracts em que o LLM não
     encontrou nenhuma entrada estruturada pra extrair.

  3. Anexa o ano de publicação a cada entrada que sobrou. O ano NÃO
     vem do modelo -- vem do próprio candidatos.csv (coluna `ano`, que
     por sua vez veio de `Publication Year` no .xls original, lido
     pelo seu regexando.py). Juntar isso por fora, depois da extração,
     é mais seguro que pedir pro LLM repetir um número que ele nem
     devia estar "lendo" do texto -- elimina de vez qualquer risco de
     o ano vir alucinado ou trocado.

Uso:
    python tratamento_basico.py
    # lê saida/extracoes.jsonl + saida/candidatos.csv
    # escreve saida/extracoes_tratadas.jsonl
"""

import json

import pandas as pd

from config import CANDIDATOS_CSV, EXTRACOES_JSONL, EXTRACOES_TRATADAS_JSONL


def tratamento_basico():
    candidatos = pd.read_csv(CANDIDATOS_CSV, index_col="i")

    linhas = []
    with EXTRACOES_JSONL.open() as f_in:
        for l in f_in:
            if not l.strip():
                continue
            linhas.append(json.loads(l))

    total_linhas = len(linhas)
    linhas.sort(key=lambda d: d["i"])

    total_entradas = 0
    sem_ano = 0
    vazias_removidas = 0

    with EXTRACOES_TRATADAS_JSONL.open("w") as f_out:
        for d in linhas:

            if not d.get("entradas"):
                vazias_removidas += 1
                continue

            if d["i"] not in candidatos.index:

                print(f"  aviso: i={d['i']} não está em candidatos.csv, pulando")
                continue

            ano = candidatos.loc[d["i"], "ano"]

            ano_limpo = None if pd.isna(ano) else int(ano)
            if ano_limpo is None:
                sem_ano += 1

            for entrada in d["entradas"]:
                entrada["ano_de_publicacao"] = ano_limpo
                total_entradas += 1

            f_out.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"{total_linhas} linhas lidas de {EXTRACOES_JSONL.name}")
    print(f"{vazias_removidas} linhas com 'entradas' vazia foram removidas")
    print(f"{total_entradas} entradas receberam ano_de_publicacao")
    if sem_ano:
        print(f"{sem_ano} abstracts candidatos não tinham 'Publication Year' "
              f"preenchido no .xls original -- ano_de_publicacao ficou null")
    print(f"salvo em: {EXTRACOES_TRATADAS_JSONL}")


if __name__ == "__main__":
    tratamento_basico()
