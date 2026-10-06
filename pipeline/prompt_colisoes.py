import json

from cliente_iluma import perguntar
from json_utils import ler_json

SISTEMA = """Você extrai dados estruturados de resumos de artigos sobre colisões
de íons pesados e física de altas energias.

Do resumo fornecido, extraia UMA entrada por par (sistema de colisão, energia)
discutido. Um resumo pode gerar zero, uma ou várias entradas.

Campos por entrada:
- especie_1, especie_2: os dois projéteis hadrônicos da colisão -- SOMENTE
  núcleos atômicos ou prótons (ex: "Pb", "Au", "Xe", "p"). Elétrons,
  pósitrons, múons, fótons e qualquer outro lépton/bóson NUNCA são espécies
  válidas (ver regra 4). Ordem alfabética sempre, não a ordem em que aparecem
  no texto. Se não especificado, use null para os dois -- não adivinhe.
- energia_valor: número da energia, exatamente como está no texto (sem converter
  unidade). Use null se o sistema de colisão é discutido mas nenhum valor
  numérico de energia é dado.
- energia_unidade: "GeV", "TeV" ou "MeV" (e variações), como aparece no texto. null se não houver
  energia_valor.
- energia_tipo: "sqrt_s_NN" (energia de centro de massa por par de núcleons),
  "energia_de_feixe", ou "nao_informado" se o tipo não estiver claro ou não
  houver energia_valor. Se o texto citar só "sqrt(s)"/"√s" (sem o subscrito
  "_NN") ou só a energia total da colisão sem qualificador (ex: "LHC 7 TeV
  p-p collisions"), classifique como "sqrt_s_NN" mesmo assim -- é a
  convenção usual da área, especialmente comum em colisões p-p onde o
  subscrito costuma ser omitido. Use "nao_informado" só quando não houver
  energia_valor, ou quando o texto for ambíguo o bastante pra não dar pra
  saber se a energia citada é de centro de massa ou de feixe.
- experimento: nome do detector/colaboração citado (ex: "ALICE", "CMS",
  "STAR"), ou null.
- acelerador: nome do acelerador citado (ex: "LHC", "RHIC"), ou null.
- instituicao: nome da instituição/laboratório dono do acelerador (ex:
  "CERN", "BNL", "Fermilab"), ou null. É diferente de acelerador e
  experimento -- é a organização, não a máquina nem o detector. Diferente de
  acelerador e experimento, ESTE campo PODE ser inferido a partir do
  acelerador ou do experimento citados no texto, mesmo que a instituição não
  seja mencionada explicitamente (ex: texto cita "LHC" ou "ALICE" -> pode
  preencher instituicao com "CERN"). Só preencha por inferência quando tiver
  certeza da associação; na dúvida, use null.
- observaveis: lista de 1 a 4 temas/grandezas físicas medidas ou discutidas
  nesta entrada. A lista é ABERTA: você escolhe os nomes, seguindo este padrão:
    * snake_case, minúsculas, sem acentos, sem espaços;
    * substantivo curto e genérico (2 a 4 palavras), descrevendo o TEMA e não
      a frase do resumo (ex: "supressao_de_jatos", não
      "supressao_de_jatos_em_colisoes_centrais_de_pb_pb");
    * NUNCA use "outro" nem "diversos" -- se nada da lista abaixo servir,
      crie um nome novo dentro do padrão;
    * seja consistente: se um tema já tem nome na lista abaixo, reuse esse
      nome em vez de inventar sinônimo.
  Nomes já usados (reuse quando o tema bater, mas não se limite a eles):
  "estranheza", "heavy_flavor", "fluxo_coletivo", "espectro_de_particulas",
  "centralidade", "supressao_de_jatos", "producao_de_quarkonia",
  "correlacoes_de_particulas", "multiplicidade", "flutuacoes_evento_a_evento",
  "producao_de_fotons", "producao_de_dileptons", "secao_de_choque",
  "polarizacao", "ressonancias", "producao_de_antimateria",
  "producao_de_hadrons_leves", "emissao_frontal".
  Exemplos de temas novos no padrão correto: texto sobre "J/psi suppression"
  -> "producao_de_quarkonia"; "HBT interferometry" -> "interferometria_hbt";
  "chiral magnetic effect" -> "efeito_magnetico_quiral".
  Inclua "centralidade" se o resumo discutir dependência com centralidade da
  colisão, mesmo sem dar números (ex: "central" vs "peripheral collisions").

Regras:
1. NÃO infira acelerador a partir do detector, nem detector a partir do
   acelerador -- mesmo que você reconheça a associação (ex: saber que ALICE
   fica no LHC não autoriza preencher acelerador="LHC" se o texto só citou
   "ALICE"). Esses dois campos só valem o que o texto escreve
   explicitamente. É melhor null do que completar com conhecimento externo.
   A ÚNICA exceção é instituicao (ver definição do campo acima), que pode
   ser inferida a partir de acelerador ou experimento citados no texto.
2. sqrt_s_NN e energia de feixe NÃO são a mesma grandeza. Nunca converta um no
   outro; registre o tipo exatamente como o texto descreve -- exceto pela
   inferência de "sqrt_s_NN" a partir de "√s" sem subscrito ou de energia
   sem qualificador, já coberta na definição de energia_tipo acima.
3. Se o resumo comparar duas energias ou dois sistemas, gere uma entrada para
   cada -- nunca registre uma diferença ou razão como se fosse um valor de
   energia.
4. FILTRO DE VALIDADE -- uma entrada só deve ser gerada se AMBAS as condições
   abaixo forem satisfeitas. Se qualquer uma falhar, responda
   {"entradas": []}:
   (a) pelo menos um entre acelerador, experimento ou instituicao ficaria
       preenchido (não os três null) -- acelerador e experimento só contam
       se citados explicitamente no texto; instituicao conta mesmo se só
       inferida a partir de um acelerador/experimento citado (regra 1); E
   (b) um sistema de colisão real de física de altas energias é nomeado no
       texto (especie_1 e especie_2 são identificáveis, ex: "Pb+Pb", "p-p",
       "Au+Au", "p+Pb" -- não vale menção incidental, nem sistemas que não
       são colisões núcleo-núcleo ou próton-próton/próton-núcleo de
       acelerador, como plasma de gás ou fontes astrofísicas).
       EXCLUSÃO EXPLÍCITA: colisões que envolvam QUALQUER lépton ou fóton
       como projétil são inválidas, mesmo que citem acelerador e experimento
       e mesmo que o resumo também mencione hádrons. Isso inclui e+e-, e-p
       (DIS, HERA), e-A (EIC), mu-p, gamma-p, gamma-gamma, neutrino-núcleo
       e colisões ultraperiféricas tratadas como fóton-alvo. Se o resumo
       tratar SÓ desses sistemas, responda {"entradas": []}. Se tratar
       desses E de um sistema válido (ex: p-p), gere entrada apenas para o
       sistema válido.
   Note que energia numérica NÃO faz parte deste filtro -- uma entrada com
   sistema e (acelerador/experimento/instituicao) identificados mas sem
   energia_valor ainda é válida (energia_valor fica null nesse caso).
5. Responda APENAS com JSON válido, sem cercas de markdown."""

EXEMPLO_ENTRADA = (
    "Au+Au data recorded by the STAR experiment at the top RHIC energy are "
    "presented. The measurements probe strangeness production in these "
    "collisions at sqrt(s_NN) = 200 GeV, with results shown as a function "
    "of centrality."
)
EXEMPLO_SAIDA = json.dumps({"entradas": [{
    "especie_1": "Au",
    "especie_2": "Au",
    "energia_valor": 200,
    "energia_unidade": "GeV",
    "energia_tipo": "sqrt_s_NN",
    "experimento": "STAR",
    "acelerador": "RHIC",
    "instituicao": "BNL",
    "observaveis": ["estranheza", "centralidade"],
}]}, ensure_ascii=False)

EXEMPLO2_ENTRADA = (
    "The LHCf experiment provides new data for very forward particle "
    "productions produced by LHC 7 TeV and 0.9 TeV p-p collisions."
)
EXEMPLO2_SAIDA = json.dumps({"entradas": [
    {
        "especie_1": "p",
        "especie_2": "p",
        "energia_valor": 7,
        "energia_unidade": "TeV",
        "energia_tipo": "sqrt_s_NN",
        "experimento": "LHCf",
        "acelerador": "LHC",
        "instituicao": "CERN",
        "observaveis": ["espectro_de_particulas"],
    },
    {
        "especie_1": "p",
        "especie_2": "p",
        "energia_valor": 0.9,
        "energia_unidade": "TeV",
        "energia_tipo": "sqrt_s_NN",
        "experimento": "LHCf",
        "acelerador": "LHC",
        "instituicao": "CERN",
        "observaveis": ["espectro_de_particulas"],
    },
]}, ensure_ascii=False)


EXEMPLO3_ENTRADA = (
    "We report measurements of hadronic event shapes in e+e- annihilation at "
    "sqrt(s) = 91.2 GeV with the ALEPH detector at LEP, and compare them to "
    "Monte Carlo predictions."
)
EXEMPLO3_SAIDA = json.dumps({"entradas": []}, ensure_ascii=False)


def extrair(resumo: str) -> list[dict]:
    bruto = perguntar([
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": EXEMPLO_ENTRADA},
        {"role": "assistant", "content": EXEMPLO_SAIDA},
        {"role": "user", "content": EXEMPLO2_ENTRADA},
        {"role": "assistant", "content": EXEMPLO2_SAIDA},
        {"role": "user", "content": EXEMPLO3_ENTRADA},
        {"role": "assistant", "content": EXEMPLO3_SAIDA},
        {"role": "user", "content": resumo},
    ], max_tokens=26000)
    return ler_json(bruto).get("entradas", [])