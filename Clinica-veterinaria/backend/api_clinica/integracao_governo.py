import os

import httpx


class IntegracaoGovernoError(Exception):
    pass


def enviar_vacinacao_antirrabica(payload: dict, chave_idempotencia: str) -> str | None:
    url = os.getenv("GOVERNO_API_URL")
    if not url:
        raise IntegracaoGovernoError(
            "Integração não configurada. Defina GOVERNO_API_URL para habilitar o envio."
        )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Idempotency-Key": chave_idempotencia,
    }
    token = os.getenv("GOVERNO_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resposta = httpx.post(url, json=payload, headers=headers, timeout=15.0)
    except httpx.HTTPError as erro:
        raise IntegracaoGovernoError(f"Falha de comunicação com a API governamental: {erro}") from erro

    if not resposta.is_success:
        detalhe = resposta.text.strip()[:500]
        raise IntegracaoGovernoError(
            f"API governamental retornou HTTP {resposta.status_code}"
            + (f": {detalhe}" if detalhe else ".")
        )

    try:
        corpo = resposta.json()
    except ValueError:
        return None

    if not isinstance(corpo, dict):
        return None

    protocolo = corpo.get("protocolo") or corpo.get("id") or corpo.get("protocol")
    return str(protocolo)[:120] if protocolo is not None else None
