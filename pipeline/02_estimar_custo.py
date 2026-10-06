"""
Estimar o custo antes de disparar o lote todo.

Rode isto ANTES do job de extração completo. Depois, rode uma dúzia de
verdade (03_rodar_lote.py --limite 12) e confira o consumo real em
Console -> Usage Logs antes de submeter o job com o lote inteiro.
"""

import pandas as pd

from config import CANDIDATOS_CSV
from prompt_colisoes import EXEMPLO_ENTRADA, EXEMPLO_SAIDA, SISTEMA


def estimar(textos, sistema=SISTEMA, exemplo=EXEMPLO_ENTRADA + EXEMPLO_SAIDA):
    """Estimativa grosseira de tokens de ENTRADA do lote inteiro.

    Regra de guardanapo: ~4 caracteres por token em inglês. Como os abstracts
    são em inglês mas o system prompt é em português, o número real tende a
    ficar um pouco acima desta estimativa -- trate como piso, não teto.
    """
    fixo = len(sistema) + len(exemplo)  # repetido em toda chamada
    chars = sum(len(t) for t in textos) + fixo * len(textos)
    tokens = chars / 4
    return len(textos), tokens


def main():
    df = pd.read_csv(CANDIDATOS_CSV, index_col="i")
    textos = df["abstract"].astype(str).tolist()

    n, tok = estimar(textos)
    print(f"candidatos: {n:5d} chamadas -- ~{tok/1000:8.0f} k tokens de entrada")
    print("\nO número real está em Console -> Usage Logs. "
          "Rode 03_rodar_lote.py --limite 12 e confira antes de submeter "
          "o job completo.")


if __name__ == "__main__":
    main()
