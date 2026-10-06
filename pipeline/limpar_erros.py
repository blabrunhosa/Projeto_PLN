"""
Limpeza pré-processada.

Este script remove do extracoes.jsonl as linhas com "erro", deixando só as
que tiveram sucesso. Depois de rodar isto, um `python 03_rodar_lote.py`
normal (sem --comeco nem --limite) vai reprocessar automaticamente só os
itens que faltam, que agora são exatamente os que tinham falhado.

Uso:
    python limpar_erros.py
"""

import json

from config import EXTRACOES_JSONL


def main():
    if not EXTRACOES_JSONL.exists():
        print(f"{EXTRACOES_JSONL} não existe -- nada a limpar.")
        return

    with EXTRACOES_JSONL.open(encoding="utf-8") as f:
        linhas = [json.loads(l) for l in f if l.strip()]

    com_erro = [l["i"] for l in linhas if "erro" in l]
    sem_erro = [l for l in linhas if "erro" not in l]

    if not com_erro:
        print("Nenhuma linha com erro encontrada -- nada a limpar.")
        return

    with EXTRACOES_JSONL.open("w", encoding="utf-8") as f:
        for linha in sem_erro:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")

    print(f"Removidas {len(com_erro)} linha(s) com erro: {sorted(com_erro)}")
    print("Agora rode: python 03_rodar_lote.py")


if __name__ == "__main__":
    main()
