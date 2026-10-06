import json, re

ARQ_ENTRADA = "../saida/extracoes_tratadas.jsonl"
ARQ_GRUPOS  = "../saida/grupos.txt"
ARQ_SAIDA   = "../saida/extracoes_agrupadas.jsonl"

mapa = {}
padrao = re.compile(r"^\s*([^\s=]+)\s*=\s*\[(.*?)\]\s*$", re.DOTALL | re.MULTILINE)

with open(ARQ_GRUPOS, encoding="utf-8") as f:
    texto = f.read()

for m in padrao.finditer(texto):
    grupo = m.group(1).strip()
    for item in m.group(2).split(","):
        item = item.strip()
        if item:
            mapa[item.lower()] = grupo
    mapa[grupo.lower()] = grupo

nomes_grupos = {g.lower() for g in mapa.values()}

def converter(lista):
    novo, vistos = [], set()
    for obs in lista:
        nome = mapa.get(obs.strip().lower(), obs)
        if nome not in vistos:
            vistos.add(nome)
            novo.append(nome)
    return novo

n_alteradas = 0
sem_grupo = set()
with open(ARQ_ENTRADA, encoding="utf-8") as fin, \
     open(ARQ_SAIDA, "w", encoding="utf-8", newline="\n") as fout:
    for linha in fin:
        if not linha.strip():
            continue
        reg = json.loads(linha)
        for ent in reg.get("entradas", []):
            antes = ent.get("observaveis") or []
            depois = converter(antes)
            if depois != antes:
                n_alteradas += 1
            ent["observaveis"] = depois
            sem_grupo.update(o for o in depois if o.lower() not in nomes_grupos)
        fout.write(json.dumps(reg, ensure_ascii=False) + "\n")

print(f"Pronto: {n_alteradas} entradas alteradas -> {ARQ_SAIDA}")
print("Sem grupo:", sorted(sem_grupo))
