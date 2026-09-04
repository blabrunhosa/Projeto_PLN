import pandas as pd
import numpy as np
import regex as re
import os
import random

CAMINHOS_ARQUIVOS = [
    'Dados\DADOS1.xls',
    'Dados\DADOS2.xls',
    'Dados\DADOS3.xls',
    'Dados\DADOS4.xls',
    'Dados\DADOS5.xls',
    'Dados\DADOS6.xls',
    'Dados\DADOS7.xls',
    'Dados\DADOS8.xls',
    'Dados\DADOS9.xls',
    'Dados\DADOS10.xls',
    'Dados\DADOS11.xls',
    'Dados\DADOS12.xls',
    'Dados\DADOS13.xls',
    'Dados\DADOS14.xls',
    'Dados\DADOS15.xls',
    'Dados\DADOS16.xls',
    'Dados\DADOS17.xls',
]

COLUNA_ABSTRACT = 'Abstract' # coluna V
COLUNA_TITULO = 'Article Title' # coluna I

ACELERADORES = ['LHC', 'Large Hadron Collider', 'RHIC', 'Relativistic Heavy Ion Collider']
DETECTORES = ['ALICE', 'CMS', 'ATLAS', 'LHCb', 'STAR', 'sPHENIX']
COLISOES_POSSIVEIS = ["Pb", "Au", "Xe", "O", "p", "d", "e\\+", "e-"]

TRACOS_UNICODE = ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]

padrao_aceleradores = re.compile(r"\b(" + "|".join(ACELERADORES) + r")\b")
padrao_detectores = re.compile(r"\b(" + "|".join(DETECTORES) + r")\b")

padrao_colisoes = re.compile(
    r"\b(" + "|".join(COLISOES_POSSIVEIS) + r")-(" + "|".join(COLISOES_POSSIVEIS) + r")\b"
)

padrao_energia = re.compile(
    r"(?:\u221a|sqrt)?\s*\(?\s*s(?:_?\{?\s*NN\s*\}?)?\s*\)?\s*=\s*(\d+(?:\.\d+)?)\s*(TeV|GeV|MeV)",
    re.IGNORECASE
)

def substituir_tracos(texto):
    # troca tudo por "-" normal
    for traco in TRACOS_UNICODE:
        texto = texto.replace(traco, "-")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def processar_abstract(abstract):
    # se não tem abstract (NaN, float, etc) devolve tudo vazio
    if pd.isna(abstract) or not isinstance(abstract, str):
        return {'aceleradores': [], 'detectores': [], 'colisoes': [], 'energia': []}

    texto = substituir_tracos(abstract)

    return {
        'aceleradores': padrao_aceleradores.findall(texto),
        'detectores': padrao_detectores.findall(texto),
        'colisoes': padrao_colisoes.findall(texto),
        'energia': padrao_energia.findall(texto),
    }

def ler_arquivo_excel(caminho):
    if not os.path.exists(caminho):
        print(f"arquivo não encontrado: {caminho}")
        return None
    tabela = pd.read_excel(caminho)
    return tabela

def processar_uma_linha(linha, indice, nome_arquivo):
    titulo = linha[COLUNA_TITULO]
    if pd.isna(titulo):
        titulo = f"Linha {indice}"

    abstract = linha[COLUNA_ABSTRACT]
    info = processar_abstract(abstract)

    tem_alguma_coisa = bool(
        info['aceleradores'] or info['detectores'] or info['colisoes'] or info['energia']
    )

    resultado = {
        'arquivo': nome_arquivo,
        'linha': indice,
        'titulo': titulo,
        'abstract': abstract if isinstance(abstract, str) else '',
        'aceleradores': info['aceleradores'],
        'detectores': info['detectores'],
        'colisoes': info['colisoes'],
        'energia': info['energia'],
        'tem_algo': tem_alguma_coisa,
    }

    return resultado

def processar_todos_os_arquivos(caminhos):
    # junta tudo em uma LISTA
    todos_resultados = []

    for caminho in caminhos:
        nome_arquivo = os.path.basename(caminho)
        print(f"No arquivo: {nome_arquivo}")

        tabela = ler_arquivo_excel(caminho)
        if tabela is None:
            continue

        for indice, linha in tabela.iterrows():
            resultado = processar_uma_linha(linha, indice, nome_arquivo)
            todos_resultados.append(resultado)

        print(f"{len(tabela)} linhas processadas")
    return todos_resultados

def mostrar_estatisticas(resultados):
    total = len(resultados)
    if total == 0:
        print("Sem resultado")
        return

    total_com_algo = sum(1 for r in resultados if r['tem_algo'])
    total_aceleradores = sum(1 for r in resultados if r['aceleradores'])
    total_detectores = sum(1 for r in resultados if r['detectores'])
    total_colisoes = sum(1 for r in resultados if r['colisoes'])
    total_energia = sum(1 for r in resultados if r['energia'])

    print()
    print("Estatísticas")
    print()
    print(f"total de abstracts: {total}")
    print(f"Com pelo menos uma informação: {total_com_algo} ({total_com_algo/total*100:.1f} %)")
    print(f"Com acelerador: {total_aceleradores} ({total_aceleradores/total*100:.1f} %)")
    print(f"Com detector: {total_detectores} ({total_detectores/total*100:.1f} %)")
    print(f"Com colisão: {total_colisoes} ({total_colisoes/total*100:.1f} %)")
    print(f"Com energia: {total_energia} ({total_energia/total*100:.1f} %)")

# para deixar o texto ok
def formatar_lista_simples(lista):
    # tira repetido e junta com
    vistos = []
    for item in lista:
        if item not in vistos:
            vistos.append(item)
    return "; ".join(vistos) if vistos else ""

def formatar_colisoes(lista_de_pares):
    formatado = [f"{a}-{b}" for a, b in lista_de_pares]
    return formatar_lista_simples(formatado)

def formatar_energia(lista_de_pares):
    formatado = [f"{valor} {unidade}" for valor, unidade in lista_de_pares]
    return formatar_lista_simples(formatado)

def montar_dataframe_final(resultados):
    linhas_relevantes = [r for r in resultados if r['tem_algo']]

    linhas_formatadas = []
    for r in linhas_relevantes:
        linha = {
            'Título': r['titulo'],
            'Abstract': r['abstract'],
            'Acelerador': formatar_lista_simples(r['aceleradores']),
            'Detector': formatar_lista_simples(r['detectores']),
            'Colisão': formatar_colisoes(r['colisoes']),
            'Energia': formatar_energia(r['energia']),
        }
        linhas_formatadas.append(linha)

    return pd.DataFrame(linhas_formatadas)

if __name__ == "__main__":
    print("PROCESSANDO OS ARQUIVOS")

    resultados = processar_todos_os_arquivos(CAMINHOS_ARQUIVOS)
    mostrar_estatisticas(resultados)

    # df completo
    df_completo = pd.DataFrame(resultados)
    df_completo.to_csv('resultados_completos.csv', index=False, encoding='utf-8-sig')
    print("Arquivo: resultados_completos.csv")

    # dataframe que importa
    df_final = montar_dataframe_final(resultados)
    df_final.to_csv('dataframe_final.csv', index=False, encoding='utf-8-sig')
    print(f"Arquivo: dataframe_final.csv ({len(df_final)} linhas)")
