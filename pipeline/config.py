"""
Configuração central do pipeline. Tudo que os outros scripts precisam
(caminhos, parâmetros de conexão) vem daqui. Assim, pra rodar no cluster
em vez de localmente, só se mexe neste arquivo.
"""

import getpass
import os
from pathlib import Path

BASE_URL = "https://iluma.cnpem.br:4000/v1"
MODELO = "iluma"
TEMPERATURA = 0.5

def obter_token() -> str:
    token = os.environ.get("ILUMA_TOKEN")
    if token:
        return token.strip()

    caminho_token = Path.home() / ".iluma_token"
    if caminho_token.exists():
        return caminho_token.read_text().strip()

    return getpass.getpass("Token da IlumA (sk-...): ")

RAIZ = Path(__file__).resolve().parent.parent 

CAMINHOS_XLS = [
    RAIZ / "Dados" / f"DADOS{i}.xls" for i in range(1, 18)
]

CANDIDATOS_CSV = RAIZ / "saida" / "candidatos.csv"
EXTRACOES_JSONL = RAIZ / "saida" / "extracoes.jsonl"
EXTRACOES_TRATADAS_JSONL = RAIZ / "saida" / "extracoes_tratadas.jsonl"
EXTRACOES_CHECADAS_CSV = RAIZ / "saida" / "extracoes_checadas.csv"
EXTRACOES_AGRUPADAS_JSONL = RAIZ / "saida" / "extracoes_agrupadas.jsonl"
EXTRACOES_EMBEDDINGS_JSONL = RAIZ / "saida" / "extracoes_embeddings.jsonl"  
AMOSTRA_REVISAO_CSV = RAIZ / "saida" / "amostra_para_revisar.csv"
EMBEDDINGS_PARQUET = RAIZ / "saida" / "embeddings.parquet"

(RAIZ / "saida").mkdir(parents=True, exist_ok=True)

PAUSA_ENTRE_CHAMADAS_S = 0.2
