# Projeto PLN — Extração de informações referentes ao estado da arte de colisões em física de altas energias

Projeto da disciplina de Processamento de Linguagem Natural (4º semestre do bacharelado em Ciência e Tecnologia da Ilum – Escola de Ciências, CNPEM).

O objetivo é servir de **visão geral e guia para quem está começando em Física de Altas Energias (HEP)**. A partir de resumos de artigos, o pipeline extrai, para cada colisão discutida, o **sistema de colisão** (p–p, p–Pb, Pb–Pb, Au–Au…), a **energia**, o **acelerador**, o **experimento**, a **instituição** e os **observáveis** estudados. Com esses dados estruturados é possível:

- analisar a evolução da área ao longo dos anos (quais sistemas e aceleradores dominam cada época);
- **buscar artigos por significado** (busca semântica), sem depender só de palavras-chave e metadados.

## Equipe

- [**Brenda Laube Abrunhosa**](https://github.com/blabrunhosa)
- [**João Henrique de Lima Gasquez**](https://github.com/ComicDeath)

## Docente

- **Profº Dr. James Moraes de Almeida**

## Estrutura do repositório

```
Projeto_PLN/
├── Dados/                      exportações .xls dos artigos (DADOS1 … DADOS17)
├── pipeline/                   scripts, na ordem de execução (prefixos 01–07)
│   ├── config.py               caminhos e parâmetros centrais (único lugar a editar)
│   ├── regexando.py            regras de regex: colisões, energias, aceleradores, detectores
│   ├── prompt_colisoes.py      prompt e chamada da LLM para a extração
│   ├── cliente_iluma.py        conexão com a IlumA (API compatível com OpenAI)
│   ├── json_utils.py           leitura tolerante de JSON devolvido pela LLM
│   ├── 01_filtrar_candidatos.py
│   ├── 02_estimar_custo.py     estimativa de tokens antes de rodar o lote
│   ├── 03_rodar_lote.py        extração com retomada (pode ser interrompida e continuada)
│   ├── limpar_erros.py         remove linhas com erro para reprocessá-las
│   ├── tratamento_basico.py
│   ├── contar_observaveis.py   lista os observáveis e quantas vezes aparecem
│   ├── agrupar_observaveis.py
│   ├── 04_checar_alucinacao.py
│   ├── ver_falhas_alucinacao.py
│   ├── 05_avaliar_amostra.py
│   ├── 06_gerar_embeddings.py
│   └── 07_buscar.py            motor de busca
├── saida/                      arquivos gerados (já incluídos, ver abaixo)
├── specter/                    adapter do SPECTER2 usado na consulta (baixado pelo 07)
└── requirements.txt
```

Todos os caminhos vêm de `pipeline/config.py`. A pasta `saida/` já contém o resultado de todas as etapas, então dá para usar a busca e as análises sem rodar a extração com a LLM.

## Visão geral do pipeline

```
Dados/DADOS*.xls                       exportações bibliográficas (título, abstract, ano)
   │  01_filtrar_candidatos.py         filtro por expressões regulares (generoso)
   ▼
saida/candidatos.csv                   abstracts candidatos, com índice estável `i`
   │  03_rodar_lote.py                 extração estruturada com uma LLM (IlumA)
   ▼
saida/extracoes.jsonl                  uma linha por abstract: {"i", "entradas": [...]}
   │  tratamento_basico.py             ordena, remove vazios, anexa o ano de publicação
   ▼
saida/extracoes_tratadas.jsonl
   │  agrupar_observaveis.py           agrupa observáveis sinônimos (saida/grupos.txt)
   ▼
saida/extracoes_agrupadas.jsonl        ← dados estruturados finais
   │  04_checar_alucinacao.py          o valor de energia extraído está no texto?
   │  05_avaliar_amostra.py            revisão manual → precisão
   │  06_gerar_embeddings.py           SPECTER2 (adapter proximity)
   ▼
saida/extracoes_embeddings.jsonl       vetores de 768 dimensões, norma L2 = 1
   │  07_buscar.py                     busca semântica por similaridade de cosseno
   ▼
resultados da busca
```

## Instalação

Clone o projeto localmente e instale as dependências listadas no `requirements.txt`

## Motor de busca

O `07_buscar.py` recebe uma consulta em linguagem natural e devolve os abstracts mais parecidos em significado, mesmo quando não compartilham as mesmas palavras.

### Como funciona

1. **Documentos.** Cada abstract (`título [SEP] abstract`) foi transformado em um vetor de 768 dimensões com o **SPECTER2**, usando o adapter `allenai/specter2` (*proximity*, indicado para representar documentos). Os vetores ficam em `saida/extracoes_embeddings.jsonl` e são normalizados (norma L2 = 1). Foram gerados pelo `06_gerar_embeddings.py`.
2. **Consulta.** O texto digitado é transformado em vetor no momento da busca, com o adapter `allenai/specter2_adhoc_query`, indicado pelo SPECTER2 para consultas curtas.
3. **Ranking.** Como os dois lados têm norma 1, o cosseno entre consulta e documento é apenas o produto escalar. A busca é uma multiplicação matriz × vetor, e devolve os `k` documentos de maior cosseno.

### Como usar

Rode de dentro da pasta `pipeline/`:

```bash
cd pipeline

# modo interativo: digite consultas até enviar uma linha vazia ou "sair"
python 07_buscar.py

# uma consulta só, com 5 resultados
python 07_buscar.py -q "quark gluon plasma elliptic flow" -k 5

# 20 resultados, abstracts completos (sem truncar em 500 caracteres)
python 07_buscar.py -k 20 --completo
```

| Opção | Efeito |
|---|---|
| `-q`, `--query` | consulta única (sem modo interativo) |
| `-k` | quantidade de resultados (padrão 10) |
| `--completo` | mostra o abstract inteiro |

Cada resultado traz a posição, o cosseno*, o índice `i` do abstract (o mesmo de `saida/candidatos.csv` e das extrações), o ano, o título e o início do abstract.

Com o `i` é possível voltar a `saida/extracoes_agrupadas.jsonl` e ver o sistema, a energia, o acelerador e os observáveis extraídos daquele artigo.

### Primeira execução

- **Precisa de internet.** O modelo base `allenai/specter2_base` é baixado do Hugging Face e guardado em cache. Depois disso, o uso é local.
- O adapter de consulta é salvo em `specter/specter2_adhoc_query/`. O download usa uma pasta local em vez do cache padrão porque, no Windows, os *symlinks* do cache falham com `WinError 1314` se o Modo Desenvolvedor não estiver ativo.
- Usa GPU se houver (`cuda`); caso contrário roda em CPU, o que é suficiente para consultas avulsas.

### Limitações

- A busca é **puramente semântica**: não filtra por sistema, energia ou ano. Esses campos estão em `extracoes_agrupadas.jsonl`, e podem ser usados para filtrar os resultados depois (usando o `i`).
- Só cobre os **1.689 abstracts com extração válida**, ou seja, os que têm um sistema de colisão hadrônico identificado. Resumos sem esse tipo de colisão ficam de fora.
- Para atualizar a base (novos dados ou nova extração), é preciso regenerar os embeddings com `python 06_gerar_embeddings.py`.

## Rodando o pipeline completo

```bash
cd pipeline
python 01_filtrar_candidatos.py     # Dados/*.xls  →  saida/candidatos.csv
python 02_estimar_custo.py          # opcional: estimativa de tokens
python 03_rodar_lote.py --limite 12 # teste com poucos abstracts; depois sem --limite
python limpar_erros.py              # se houve falhas: remove-as e rode o 03 de novo
python tratamento_basico.py         # → saida/extracoes_tratadas.jsonl
python contar_observaveis.py ../saida/extracoes_tratadas.jsonl   # ajuda a montar saida/grupos.txt
python agrupar_observaveis.py       # → saida/extracoes_agrupadas.jsonl
python 04_checar_alucinacao.py      # → saida/extracoes_checadas.csv
python ver_falhas_alucinacao.py     # inspeciona o que não conferiu
python 05_avaliar_amostra.py        # revisão manual interativa → precisão
python 06_gerar_embeddings.py       # → saida/extracoes_embeddings.jsonl
python 07_buscar.py                 # busca
```

### Extração com a LLM (passo 03)

A extração usa a **IlumA**, a LLM do CNPEM (`pipeline/config.py` define `BASE_URL` e `MODELO`), que só é acessível a quem tem token e rede do CNPEM. O token é lido, nesta ordem, da variável de ambiente `ILUMA_TOKEN`, do arquivo `~/.iluma_token` ou digitado no terminal. Não coloque o token no repositório.

Quem não tem acesso pode pular os passos 02 e 03, porque `saida/extracoes.jsonl` já está no repositório e todos os passos seguintes funcionam a partir dele.

O `03_rodar_lote.py` grava uma linha por abstract e retoma de onde parou se a rede cair ou o job for interrompido.

### Como a extração é guiada

O prompt (`prompt_colisoes.py`) define uma entrada por par (sistema de colisão, energia) e pede, em JSON, `especie_1`, `especie_2`, `energia_valor`, `energia_unidade`, `energia_tipo`, `experimento`, `acelerador`, `instituicao` e `observaveis`. Regras importantes:

- **Acelerador e experimento só valem o que está escrito no texto**, sem completar com conhecimento externo. A instituição pode ser inferida (ex.: LHC → CERN).
- Só colisões **hádron–hádron** (p, íons) são válidas; e⁺e⁻, DIS e colisões com fótons são descartadas.
- Resumo sem sistema identificável devolve `{"entradas": []}`, e essas linhas são removidas no `tratamento_basico.py`.

O **ano de publicação não vem da LLM**: é anexado depois, a partir do `candidatos.csv`, para evitar anos inventados.

## Avaliação da qualidade

1. **Checagem de alucinação** (`04_checar_alucinacao.py`). Verifica se o `energia_valor` extraído aparece no abstract de origem, com normalização de artefatos de OCR (`5:02` → `5.02`, `2 . 76` → `2.76`). Resultado atual: 1.647 de 1.649 (99,9%). Para inspecionar as falhas, use `ver_falhas_alucinacao.py`.
2. **Precisão por revisão manual** (`05_avaliar_amostra.py`). Mostra um abstract por vez, ao lado das extrações feitas, e pergunta se está tudo certo (`s`/`n`/`p`/`q`). As respostas ficam em `saida/revisao.jsonl` (o script pode ser interrompido e retomado), e ao final imprime a precisão. Cada julgamento vale por abstract: basta uma entrada errada para marcar `n`, o que torna a métrica mais rigorosa do que contar entrada por entrada.

Observação: a checagem de alucinação confirma que o **número** está no texto, mas não que ele foi associado ao sistema de colisão correto. Essa parte é medida pela precisão manual.

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
