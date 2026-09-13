import pandas as pd
import ast

# CONFIGURAÇÕES
ARQUIVO_ENTRADA = 'resultados_completos.csv'
ARQUIVO_SAIDA = 'resultados_filtrados.csv'

FILTROS_ATIVOS = {
    'aceleradores':     True,
    'detectores':       True,
    'colisoes':         True,
    'energia':          True,
    'estranheza':       False,
    'heavy_flavor':     False,
    'tipos_particula':  False,
    'centralidade':     False,
}

MODO_COMBINACAO = 'E'

# convertidas de volta pra lista de verdade antes de filtrar
COLUNAS_LISTA = [
    'aceleradores', 'detectores', 'colisoes', 'energia',
    'tipos_particula', 'centralidade',
]

# não precisam de conversão
COLUNAS_BOOLEANAS = ['estranheza', 'heavy_flavor']


def carregar_dataframe(caminho):
    df = pd.read_csv(caminho)

    for coluna in COLUNAS_LISTA:
        if coluna not in df.columns:
            continue
        df[coluna] = df[coluna].apply(converter_texto_em_lista)

    return df


def converter_texto_em_lista(valor):
    # células vazias/NaN viram lista vazia
    if pd.isna(valor):
        return []
    # se já é lista/tupla (não deveria acontecer vindo de CSV, mas por garantia)
    if isinstance(valor, (list, tuple)):
        return list(valor)
    # string tipo "['ALICE', 'CMS']" ou "[('Pb', 'Pb')]" -> lista de verdade
    try:
        resultado = ast.literal_eval(valor)
        if isinstance(resultado, (list, tuple)):
            return list(resultado)
        return [resultado]
    except (ValueError, SyntaxError):
        return []


def coluna_tem_valor(df, coluna):
    """Devolve uma série booleana: True nas linhas onde essa coluna 'tem algo'."""
    if coluna in COLUNAS_BOOLEANAS:
        return df[coluna].fillna(False).astype(bool)
    else:
        return df[coluna].apply(lambda lista: len(lista) > 0)


def montar_filtro(df):
    criterios_ligados = [nome for nome, ligado in FILTROS_ATIVOS.items() if ligado]

    if not criterios_ligados:
        raise ValueError("Nenhum filtro está ligado em FILTROS_ATIVOS. Ligue pelo menos um.")

    mascaras = [coluna_tem_valor(df, coluna) for coluna in criterios_ligados]

    if MODO_COMBINACAO == 'E':
        filtro_final = mascaras[0]
        for m in mascaras[1:]:
            filtro_final = filtro_final & m
    elif MODO_COMBINACAO == 'OU':
        filtro_final = mascaras[0]
        for m in mascaras[1:]:
            filtro_final = filtro_final | m
    else:
        raise ValueError("MODO_COMBINACAO precisa ser 'E' ou 'OU'.")

    return filtro_final, criterios_ligados


if __name__ == "__main__":
    df = carregar_dataframe(ARQUIVO_ENTRADA)
    filtro, criterios_ligados = montar_filtro(df)

    df_filtrado = df[filtro]

    print(f"Critérios usados ({MODO_COMBINACAO}): {', '.join(criterios_ligados)}")
    print(f"Linhas no arquivo original: {len(df)}")
    print(f"Linhas depois do filtro: {len(df_filtrado)}")

    df_filtrado.to_csv(ARQUIVO_SAIDA, index=False, encoding='utf-8-sig')
    print(f"Arquivo salvo: {ARQUIVO_SAIDA}")
