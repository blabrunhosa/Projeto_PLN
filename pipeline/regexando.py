import pandas as pd
import numpy as np
import regex as re
import os
import random

CAMINHOS_ARQUIVOS = [
    'Dados\\DADOS1.xls',
    'Dados\\DADOS2.xls',
    'Dados\\DADOS3.xls',
    'Dados\\DADOS4.xls',
    'Dados\\DADOS5.xls',
    'Dados\\DADOS6.xls',
    'Dados\\DADOS7.xls',
    'Dados\\DADOS8.xls',
    'Dados\\DADOS9.xls',
    'Dados\\DADOS10.xls',
    'Dados\\DADOS11.xls',
    'Dados\\DADOS12.xls',
    'Dados\\DADOS13.xls',
    'Dados\\DADOS14.xls',
    'Dados\\DADOS15.xls',
    'Dados\\DADOS16.xls',
    'Dados\\DADOS17.xls',
]

COLUNA_ABSTRACT = 'Abstract'
COLUNA_TITULO = 'Article Title'
COLUNA_ANO = 'Publication Year'

ACELERADORES = [
    'LHC', 'Large Hadron Collider', 'RHIC', 'Relativistic Heavy Ion Collider',
    'SPS', 'Super Proton Synchrotron', 'FAIR', 'NICA', 'J-PARC'
]

DETECTORES = [
    'ALICE', 'CMS', 'ATLAS', 'LHCb',
    'STAR', 'sPHENIX', 'PHENIX', 'BRAHMS', 'PHOBOS',
    'NA61/SHINE', 'NA49', 'HADES',
    'CBM', 'MPD', 'BM@N',
    'BESIII', 'COMPASS', 'HERMES',
]

INSTITUICOES = [
    'CERN', 'European Organization for Nuclear Research',
    'BNL', 'Brookhaven National Laboratory', 'Brookhaven',
    'Fermilab', 'Fermi National Accelerator Laboratory', 'FNAL',
    'GSI', 'GSI Helmholtzzentrum', 'Helmholtz Centre for Heavy Ion Research',
    'JINR', 'Joint Institute for Nuclear Research',
    'KEK', 'High Energy Accelerator Research Organization',
    'SLAC', 'SLAC National Accelerator Laboratory',
    'DESY', 'Deutsches Elektronen-Synchrotron',
    'INFN', 'Istituto Nazionale di Fisica Nucleare',
    'RIKEN', 'J-PARC Center',
]

TRACOS_UNICODE = ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]

SUPERSCRITOS = {
    "\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3", "\u2074": "4",
    "\u2075": "5", "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9",
}

NUCLEOS = [
    "Pb", "Au", "Xe", "Kr", "Ar", "Ne", "He",
    "Cu", "U", "Ru", "Zr", "Ag", "In", "Sn", "La", "Ta", "Bi",
    "Ca", "Fe", "Ni", "Sm", "Gd", "Al", "Si", "O", "N", "C",
]
PARTICULAS_LEVES = ["d", "t", "p", "n", "e\\+", "e-", "\u03b1"]

ESPECIES_COLISAO = NUCLEOS + PARTICULAS_LEVES

MASSA_OPCIONAL = r"(?:\d{1,3})?"
TOKEN_COLISAO = r"(" + MASSA_OPCIONAL + r"(?:" + "|".join(ESPECIES_COLISAO) + r"))"
SEPARADOR_COLISAO = r"(?:\s*[-+]\s*|\s+on\s+)?"

padrao_colisoes = re.compile(
    r"\b" + TOKEN_COLISAO + SEPARADOR_COLISAO + TOKEN_COLISAO + r"\b"
)

DISTANCIA_PALAVRAS_COLISAO = 8
padrao_contexto_colisao = re.compile(
    r"collisions?|collide[sd]?|reaction|interactions?|scattering",
    re.IGNORECASE
)

DISTANCIA_PALAVRAS_CENTRALIDADE = 10
padrao_centralidade = re.compile(
    r"(?:"
    rf"(?<=\bcentrality\b(?:\W+\w+){{0,{DISTANCIA_PALAVRAS_CENTRALIDADE}}}\W)"
    r"|"
    rf"(?=\w+(?:\W+\w+){{0,{DISTANCIA_PALAVRAS_CENTRALIDADE}}}\W+centrality\b)"
    r")"
    r"\b(\d{1,3}\s*-\s*\d{1,3}\s*%|most central|mid-central|semi-central|central|peripheral)",
    re.IGNORECASE
)

padrao_aceleradores = re.compile(r"\b(" + "|".join(ACELERADORES) + r")\b")
padrao_detectores = re.compile(r"\b(" + "|".join(DETECTORES) + r")\b")

# ordena do maior para o menor: numa alternância o regex pega a primeira opção
# que casa, então sem isso 'GSI' engoliria 'GSI Helmholtzzentrum' e
# 'Brookhaven' engoliria 'Brookhaven National Laboratory'
padrao_instituicoes = re.compile(
    r"\b(" + "|".join(sorted(INSTITUICOES, key=len, reverse=True)) + r")\b"
)

padrao_energia = re.compile(
    r"(?:\u221a|sqrt)?\s*\(?\s*s(?:_?\{?\s*NN\s*\}?)?\s*\)?\s*=\s*(\d+(?:\.\d+)?)\s*(TeV|GeV|MeV)",
    re.IGNORECASE
)

TERMOS_ESTRANHEZA = [
    'strangeness', 'strange quark', 'hyperon', 'Lambda', '\u039b',
    'Xi', '\u039e', 'Omega', '\u03a9', 'kaon', 'K0', 'K\\+', 'K-'
]

TERMOS_HEAVY_FLAVOR = [
    'heavy flavor', 'heavy-flavor', 'heavy flavour', 'heavy-flavour',
    'charm', 'bottom', 'beauty', 'J/\u03c8', 'J/psi', 'Upsilon', '\u03a5',
    'D meson', 'D0', 'B meson', 'open charm', 'open beauty'
]

TIPOS_PARTICULA = {
    'Méson': ['pion', 'kaon', 'J/\u03c8', 'J/psi', 'D meson', 'B meson',
              'phi meson', 'rho meson', 'Upsilon', '\u03a5', 'K0'],
    'Bárion': ['proton', 'neutron', 'Lambda', '\u039b', 'Xi', '\u039e',
               'Omega', '\u03a9', 'hyperon', 'Sigma', '\u03a3'],
    'Lépton': ['electron', 'positron', 'muon', 'tau lepton', 'neutrino'],
    'Bóson': ['photon', 'gluon', 'W boson', 'Z boson', 'Higgs'],
}

padrao_estranheza = re.compile(r"\b(" + "|".join(TERMOS_ESTRANHEZA) + r")\b", re.IGNORECASE)
padrao_heavy_flavor = re.compile(r"\b(" + "|".join(TERMOS_HEAVY_FLAVOR) + r")\b", re.IGNORECASE)

padroes_tipo_particula = {
    tipo: re.compile(r"\b(" + "|".join(termos) + r")\b", re.IGNORECASE)
    for tipo, termos in TIPOS_PARTICULA.items()
}


def normalizar_texto(texto):
    for traco in TRACOS_UNICODE:
        texto = texto.replace(traco, "-")
    for sobrescrito, normal in SUPERSCRITOS.items():
        texto = texto.replace(sobrescrito, normal)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def identificar_tipos_particula(texto):
    tipos_encontrados = []
    for tipo, padrao in padroes_tipo_particula.items():
        if padrao.search(texto):
            tipos_encontrados.append(tipo)
    return tipos_encontrados


def contexto_indica_colisao(texto, inicio, fim):
    antes = texto[:inicio].split()[-DISTANCIA_PALAVRAS_COLISAO:]
    depois = texto[fim:].split()[:DISTANCIA_PALAVRAS_COLISAO]
    janela = " ".join(antes + depois)
    return bool(padrao_contexto_colisao.search(janela))


def extrair_colisoes(texto):
    pares_validos = []
    pares_duvidosos = []
    for m in padrao_colisoes.finditer(texto):
        par = (m.group(1), m.group(2))
        if contexto_indica_colisao(texto, m.start(), m.end()):
            pares_validos.append(par)
        else:
            pares_duvidosos.append(par)
    return pares_validos, pares_duvidosos


def processar_abstract(abstract):
    if pd.isna(abstract) or not isinstance(abstract, str):
        return {
            'aceleradores': [], 'detectores': [], 'instituicoes': [],
            'colisoes': [], 'colisoes_duvidosas': [],
            'energia': [], 'estranheza': False, 'heavy_flavor': False,
            'tipos_particula': [], 'centralidade': [],
        }

    texto = normalizar_texto(abstract)
    colisoes_validas, colisoes_duvidosas = extrair_colisoes(texto)

    return {
        'aceleradores': padrao_aceleradores.findall(texto),
        'detectores': padrao_detectores.findall(texto),
        'instituicoes': padrao_instituicoes.findall(texto),
        'colisoes': colisoes_validas,
        'colisoes_duvidosas': colisoes_duvidosas,
        'energia': padrao_energia.findall(texto),
        'estranheza': bool(padrao_estranheza.search(texto)),
        'heavy_flavor': bool(padrao_heavy_flavor.search(texto)),
        'tipos_particula': identificar_tipos_particula(texto),
        'centralidade': padrao_centralidade.findall(texto),
    }


def ler_arquivo_excel(caminho):
    if not os.path.exists(caminho):
        print(f"arquivo não encontrado: {caminho}")
        return None
    tabela = pd.read_excel(caminho)
    return tabela


def extrair_ano(linha):
    if COLUNA_ANO not in linha or pd.isna(linha[COLUNA_ANO]):
        return None
    try:
        return int(linha[COLUNA_ANO])
    except (ValueError, TypeError):
        return None


def processar_uma_linha(linha, indice, nome_arquivo):
    titulo = linha[COLUNA_TITULO]
    if pd.isna(titulo):
        titulo = f"Linha {indice}"

    abstract = linha[COLUNA_ABSTRACT]
    info = processar_abstract(abstract)
    ano = extrair_ano(linha)

    tem_alguma_coisa = bool(
        info['aceleradores'] or info['detectores'] or info['colisoes']
        or info['colisoes_duvidosas'] or info['energia']
        or info['estranheza'] or info['heavy_flavor'] or info['tipos_particula']
        or info['centralidade']
    )

    resultado = {
        'arquivo': nome_arquivo,
        'linha': indice,
        'titulo': titulo,
        'abstract': abstract if isinstance(abstract, str) else '',
        'ano': ano,
        'aceleradores': info['aceleradores'],
        'detectores': info['detectores'],
        'instituicoes': info['instituicoes'],
        'colisoes': info['colisoes'],
        'colisoes_duvidosas': info['colisoes_duvidosas'],
        'energia': info['energia'],
        'estranheza': info['estranheza'],
        'heavy_flavor': info['heavy_flavor'],
        'tipos_particula': info['tipos_particula'],
        'centralidade': info['centralidade'],
        'tem_algo': tem_alguma_coisa,
    }

    return resultado


def processar_todos_os_arquivos(caminhos):
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
    total_colisoes_duvidosas = sum(1 for r in resultados if r['colisoes_duvidosas'])
    total_energia = sum(1 for r in resultados if r['energia'])
    total_estranheza = sum(1 for r in resultados if r['estranheza'])
    total_heavy_flavor = sum(1 for r in resultados if r['heavy_flavor'])
    total_tipo_particula = sum(1 for r in resultados if r['tipos_particula'])
    total_centralidade = sum(1 for r in resultados if r['centralidade'])

    print()
    print("Estatísticas")
    print()
    print(f"total de abstracts: {total}")
    print(f"Com pelo menos uma informação: {total_com_algo} ({total_com_algo/total*100:.1f} %)")
    print(f"Com acelerador: {total_aceleradores} ({total_aceleradores/total*100:.1f} %)")
    print(f"Com detector: {total_detectores} ({total_detectores/total*100:.1f} %)")
    print(f"Com colisão (confirmada por contexto): {total_colisoes} ({total_colisoes/total*100:.1f} %)")
    print(f"Com colisão DUVIDOSA (sem contexto por perto): {total_colisoes_duvidosas} ({total_colisoes_duvidosas/total*100:.1f} %)")
    print(f"Com energia: {total_energia} ({total_energia/total*100:.1f} %)")
    print(f"Com estranheza: {total_estranheza} ({total_estranheza/total*100:.1f} %)")
    print(f"Com heavy-flavour: {total_heavy_flavor} ({total_heavy_flavor/total*100:.1f} %)")
    print(f"Com tipo de partícula identificado: {total_tipo_particula} ({total_tipo_particula/total*100:.1f} %)")
    print(f"Com centralidade: {total_centralidade} ({total_centralidade/total*100:.1f} %)")


def formatar_lista_simples(lista):
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
            'Ano': r['ano'],
            'Abstract': r['abstract'],
            'Acelerador': formatar_lista_simples(r['aceleradores']),
            'Detector': formatar_lista_simples(r['detectores']),
            'Colisão': formatar_colisoes(r['colisoes']),
            'Colisão (duvidosa)': formatar_colisoes(r['colisoes_duvidosas']),
            'Energia': formatar_energia(r['energia']),
            'Estranheza': r['estranheza'],
            'Heavy-flavour': r['heavy_flavor'],
            'Tipo': formatar_lista_simples(r['tipos_particula']),
            'Centralidade': formatar_lista_simples(r['centralidade']),
        }
        linhas_formatadas.append(linha)

    return pd.DataFrame(linhas_formatadas)


if __name__ == "__main__":
    print("PROCESSANDO OS ARQUIVOS")

    resultados = processar_todos_os_arquivos(CAMINHOS_ARQUIVOS)
    mostrar_estatisticas(resultados)

    df_completo = pd.DataFrame(resultados)
    df_completo.to_csv('resultados_completos.csv', index=False, encoding='utf-8-sig')
    print("Arquivo: resultados_completos.csv")

    df_final = montar_dataframe_final(resultados)
    df_final.to_csv('dataframe_final.csv', index=False, encoding='utf-8-sig')
    print(f"Arquivo: dataframe_final.csv ({len(df_final)} linhas)")

    linhas_com_centralidade = [r for r in resultados if r['centralidade']]
    with open('abstracts_com_centralidade.txt', 'w', encoding='utf-8') as f:
        for r in linhas_com_centralidade:
            f.write(f"Título: {r['titulo']}\n")
            f.write(f"Arquivo: {r['arquivo']} | Linha: {r['linha']}\n")
            f.write(f"Centralidade encontrada: {formatar_lista_simples(r['centralidade'])}\n")
            f.write(f"Abstract: {r['abstract']}\n")
            f.write("-" * 80 + "\n\n")
    print(f"Arquivo: abstracts_com_centralidade.txt ({len(linhas_com_centralidade)} abstracts)")