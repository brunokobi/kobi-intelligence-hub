"""Lista de modelos gratuitos do OpenRouter, ordenados por tamanho de
contexto -- usada pro fallback automático quando o modelo configurado
está sobrecarregado/indisponível (gotcha conhecido: modelos :free do
OpenRouter têm pool compartilhado que às vezes satura). Não resolve o
limite diário da conta inteira (isso só reseta ou pede crédito), só
sobrecarga pontual de um modelo específico.

Mesma lógica replicada em bpmn-assistant e rcm-api (serviços
independentes, sem pacote Python compartilhado entre eles)."""
import time

import requests

_cache: dict = {"modelos": None, "expira_em": 0}


def obter_modelos_gratis_openrouter(max_modelos: int = 6) -> list[str]:
    agora = time.time()
    if _cache["modelos"] and agora < _cache["expira_em"]:
        return _cache["modelos"]

    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", timeout=15)
        resp.raise_for_status()
        dados = resp.json().get("data", [])

        gratis = []
        for m in dados:
            model_id = m.get("id", "")
            pricing = m.get("pricing", {})
            try:
                gratuito = float(pricing.get("prompt", "1")) == 0 and float(pricing.get("completion", "1")) == 0
            except (TypeError, ValueError):
                gratuito = False
            if model_id.endswith(":free") and gratuito:
                gratis.append(m)

        gratis.sort(key=lambda m: m.get("context_length") or 0, reverse=True)
        modelos = [m["id"] for m in gratis[:max_modelos]]

        if modelos:
            _cache["modelos"] = modelos
            _cache["expira_em"] = agora + 3600
        return modelos or _cache["modelos"] or []
    except Exception:
        return _cache["modelos"] or []
