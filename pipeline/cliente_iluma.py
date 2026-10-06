"""
Conexão com a IlumA.

O token vem de config.obter_token(),
que funciona tanto rodando local (getpass) quanto em job de cluster
(variável de ambiente ou arquivo), em vez de sempre pedir digitado.
"""

from openai import OpenAI

from config import BASE_URL, MODELO, TEMPERATURA, obter_token

_cliente = None


def obter_cliente() -> OpenAI:
    """Cria o cliente uma única vez por processo (lazy singleton)."""
    global _cliente
    if _cliente is None:
        _cliente = OpenAI(
            base_url=BASE_URL,
            api_key=obter_token(),
            timeout=600.0,
            max_retries=1,
        )
    return _cliente


def perguntar(mensagens, **kw) -> str:
    kw.setdefault("temperature", TEMPERATURA)
    cliente = obter_cliente()
    r = cliente.chat.completions.create(model=MODELO, messages=mensagens, **kw)
    escolha = r.choices[0]
    conteudo = escolha.message.content
    if not conteudo:
        raise ValueError(f"resposta vazia (finish_reason={escolha.finish_reason})")
    if escolha.finish_reason == "length":
        raise ValueError("resposta cortada por limite de tokens")
    return conteudo


if __name__ == "__main__":
    # teste rápido de conexão -- rode `python cliente_iluma.py` antes de
    # submeter qualquer job, pra confirmar que o token está configurado certo
    print(perguntar([{"role": "user", "content": "Responda apenas: conexão OK."}]))
