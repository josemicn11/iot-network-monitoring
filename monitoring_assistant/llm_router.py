import json
import re
import requests
import unicodedata
from typing import Optional

from config import OLLAMA_URL, OLLAMA_MODEL


# Host aliases accepted by the LLM router
HOST_ALIASES = {
    "raspberry": "raspberry",
    "raspi": "raspberry",
    "rpi": "raspberry",
    "pc": "ASUS_Josemi",
    "asus": "ASUS_Josemi",
    "asus_josemi": "ASUS_Josemi",
    "ordenador": "ASUS_Josemi",
}

SUPPORTED_HOSTS = ["raspberry", "ASUS_Josemi"]


# Intents that the LLM router is allowed to return
ALLOWED_INTENTS = {
    "host_status",
    "hosts_status",
    "cpu_status",
    "cpu_compare_hosts",
    "dns_top_domains",
    "dns_top_clients",
    "dns_active_clients_list",
    "dns_summary",
    "dns_total_queries",
    "dns_domain_query_count",
    "dns_query_type_count",
    "dns_qps",
    "dns_blocked_pct",
    "dns_cached_pct",
    "dns_active_clients_count",
    "dns_query_types_summary",
    "dns_forwarded_vs_cached_summary",
    "dns_forwarded_count",
    "dns_cached_count",
    "ram_status",
    "ram_compare_hosts",
    "ram_used_pct",
    "ram_available",
    "disk_used_pct",
    "disk_status",
    "disk_compare_hosts",
    "unknown",
}


SYSTEM_PROMPT = """
You are a semantic router for a monitoring assistant.

Your task is NOT to answer the user.
Your task is to classify the user query into one allowed intent and extract relevant fields.

Return ONLY a valid JSON object.

Schema:
{
  "intent": "string",
  "host": "string or null",
  "hosts": [],
  "time_range": "string or null",
  "metric_focus": "string or null",
  "top_n": "integer or null",
  "domain": "string or null",
  "query_type": "string or null",
  "compare_mode": "max|min|null",
  "confidence": "number or null"
}

Allowed intents:
host_status
hosts_status
cpu_status
cpu_compare_hosts
dns_summary
dns_total_queries
dns_qps
dns_blocked_pct
dns_cached_pct
dns_active_clients_count
dns_active_clients_list
dns_top_domains
dns_top_clients
dns_query_types_summary
dns_forwarded_vs_cached_summary
dns_forwarded_count
dns_cached_count
dns_domain_query_count
dns_query_type_count
ram_status
ram_compare_hosts
ram_used_pct
ram_available
disk_status
disk_used_pct
disk_compare_hosts
unknown

Allowed hosts:
raspberry
ASUS_Josemi

Rules:
- Correct obvious spelling mistakes in Spanish.
- Interpret natural paraphrases.
- Use previous context if the query is a follow-up.
- If the user asks about "how DNS has gone", "estado del trafico DNS", or "si el DNS ha ido bien", use dns_summary.
- If the user compares RAM or memory across hosts, use ram_compare_hosts.
- If the user compares disk/storage across hosts, use disk_compare_hosts.
- If the user compares CPU/load across hosts, use cpu_compare_hosts.
- If the user mentions a concrete domain like youtube.com, extract it in "domain".
- If the user mentions a DNS query type like A, AAAA, PTR, TXT, HTTPS, extract it in "query_type".
- If the user asks "which host is worse" in a comparison, usually use compare_mode = "max".
- If the meaning is truly unclear, use unknown.
- Never invent unsupported intents.
"""


def normalize_text(text: str) -> str:
    # Normalize the user input before applying local checks
    text = text.lower().strip()

    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detect_all_hosts(text: str):
    # Detect all supported hosts mentioned in the query
    words = text.split()
    detected_hosts = []

    for alias, canonical_host in HOST_ALIASES.items():
        alias_words = alias.split()

        match = False

        if len(alias_words) == 1:
            if alias in words:
                match = True
        else:
            if alias in text:
                match = True

        if match and canonical_host not in detected_hosts:
            detected_hosts.append(canonical_host)

    return detected_hosts


def detect_dynamic_time_range(text: str, default: str = "-6h") -> str:
    # Convert natural time expressions into Flux-compatible ranges
    text = text.lower().strip()

    def _to_flux_duration(value: float, unit: str) -> str:
        if unit == "m":
            return f"-{int(round(value))}m"

        if unit == "h":
            total_minutes = int(round(value * 60))

            if total_minutes % 60 == 0:
                return f"-{total_minutes // 60}h"

            return f"-{total_minutes}m"

        if unit == "d":
            total_hours = int(round(value * 24))

            if total_hours % 24 == 0:
                return f"-{total_hours // 24}d"

            return f"-{total_hours}h"

        if unit == "w":
            total_days = int(round(value * 7))

            if total_days % 7 == 0:
                return f"-{total_days // 7}w"

            return f"-{total_days}d"

        if unit == "mo":
            total_days = int(round(value * 30))

            if total_days % 30 == 0:
                return f"-{total_days // 30}mo"

            return f"-{total_days}d"

        if unit == "y":
            total_days = int(round(value * 365))

            if total_days % 365 == 0:
                return f"-{total_days // 365}y"

            return f"-{total_days}d"

        return default

    unit_map = {
        "m": "m",
        "min": "m",
        "mins": "m",
        "minuto": "m",
        "minutos": "m",
        "h": "h",
        "hora": "h",
        "horas": "h",
        "d": "d",
        "dia": "d",
        "dias": "d",
        "w": "w",
        "semana": "w",
        "semanas": "w",
        "mo": "mo",
        "mes": "mo",
        "meses": "mo",
        "y": "y",
        "ano": "y",
        "anos": "y",
    }

    if any(x in text for x in [
        "ahora mismo",
        "ahora",
        "actualmente",
        "actual",
        "en este momento",
        "en este instante",
    ]):
        return "-5m"

    if any(x in text for x in [
        "de hoy",
        "hoy",
        "del dia",
        "durante el dia",
    ]):
        return "today"

    special_cases = [
        (r"\bmedia hora\b", "-30m"),
        (r"\bhora y media\b|\buna hora y media\b", "-90m"),
        (r"\bmedio dia\b", "-12h"),
        (r"\bdia y medio\b|\bun dia y medio\b", "-36h"),
        (r"\bmedia semana\b", "-4d"),
        (r"\bsemana y media\b|\buna semana y media\b", "-11d"),
        (r"\bmedio mes\b", "-15d"),
        (r"\bmes y medio\b|\bun mes y medio\b", "-45d"),
        (r"\bmedio ano\b", "-6mo"),
        (r"\bano y medio\b|\bun ano y medio\b", "-18mo"),
        (r"\bultima hora\b", "-1h"),
        (r"\bultimo dia\b", "-1d"),
        (r"\bultima semana\b", "-1w"),
        (r"\bultimo mes\b", "-1mo"),
        (r"\bultimo ano\b", "-1y"),
        (r"\bultimos minutos\b", "-15m"),
        (r"\bultimas horas\b", "-6h"),
        (r"\bultimos dias\b", "-7d"),
        (r"\bultimas semanas\b", "-4w"),
        (r"\bultimos meses\b", "-3mo"),
        (r"\bultimos anos\b", "-1y"),
    ]

    for pattern, result in special_cases:
        if re.search(pattern, text):
            return result

    numeric_patterns = [
        r"\ben\s+los\s+ultim[oa]s?\s+(\d+(?:[.,]\d+)?)\s*(min|mins|minuto|minutos|m|hora|horas|h|dia|dias|d|semana|semanas|w|mes|meses|mo|ano|anos|y)\b",
        r"\bultim[oa]s?\s+(\d+(?:[.,]\d+)?)\s*(min|mins|minuto|minutos|m|hora|horas|h|dia|dias|d|semana|semanas|w|mes|meses|mo|ano|anos|y)\b",
        r"\bdesde\s+hace\s+(\d+(?:[.,]\d+)?)\s*(min|mins|minuto|minutos|m|hora|horas|h|dia|dias|d|semana|semanas|w|mes|meses|mo|ano|anos|y)\b",
        r"\bhace\s+(\d+(?:[.,]\d+)?)\s*(min|mins|minuto|minutos|m|hora|horas|h|dia|dias|d|semana|semanas|w|mes|meses|mo|ano|anos|y)\b",
        r"\ben\s+la\s+ultima\s+(\d+(?:[.,]\d+)?)\s*(hora|horas|h|semana|semanas|w)\b",
        r"\ben\s+el\s+ultimo\s+(\d+(?:[.,]\d+)?)\s*(dia|dias|d|mes|meses|mo|ano|anos|y)\b",
    ]

    for pattern in numeric_patterns:
        match = re.search(pattern, text)

        if match:
            raw_value = match.group(1).replace(",", ".")
            value = float(raw_value)

            raw_unit = match.group(2)
            unit = unit_map.get(raw_unit)

            if unit:
                return _to_flux_duration(value, unit)

    compact_unit_map = {
        "m": "m",
        "h": "h",
        "d": "d",
        "w": "w",
        "mo": "mo",
        "y": "y",
    }

    for suffix, unit in compact_unit_map.items():
        match = re.search(
            rf"\b(\d+(?:[.,]\d+)?){suffix}\b",
            text
        )

        if match and any(word in text for word in [
            "ultimo",
            "ultima",
            "ultimos",
            "ultimas",
            "hace",
            "desde",
        ]):
            value = float(
                match.group(1).replace(",", ".")
            )

            return _to_flux_duration(value, unit)

    return default


def detect_top_n(text: str, default: int = 1) -> int:
    # Detect the number of results requested by the user
    patterns = [
        r"\btop\s+(\d+)\b",
        r"\blista\s+de\s+(\d+)\b",
        r"\b(\d+)\s+dominios?\b",
        r"\b(\d+)\s+clientes?\b",
        r"\b(\d+)\s+tipos?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return max(1, min(int(match.group(1)), 20))

    if (
        "top dominios" in text
        or "dominios mas consultados" in text
        or "dominios mas usados" in text
    ):
        return 5

    if (
        "top clientes" in text
        or "clientes mas activos" in text
    ):
        return 5

    if (
        "tipos dns" in text
        or "tipos de consulta" in text
    ):
        return 5

    return default


def _safe_fallback(
    user_input: str,
    normalized: str,
    host=None,
    hosts=None
) -> dict:
    # Return a controlled response when the LLM output cannot be used
    return {
        "ok": False,
        "intent": None,
        "host": host,
        "hosts": hosts or [],
        "time_range": None,
        "top_n": None,
        "raw_text": user_input,
        "normalized_text": normalized,
        "error": "No se ha podido interpretar la consulta con el router LLM."
    }


def _build_prompt(
    user_query: str,
    last_context: Optional[dict] = None
) -> str:
    # Build the context passed to the LLM router
    context_block = {
        "last_intent": None,
        "last_host": None,
        "last_hosts": [],
        "last_time_range": None,
        "last_domain": None,
        "last_query_type": None,
    }

    if last_context:
        context_block.update({
            "last_intent": last_context.get("intent"),
            "last_host": last_context.get("host"),
            "last_hosts": last_context.get("hosts", []),
            "last_time_range": last_context.get("time_range"),
            "last_domain": last_context.get("domain"),
            "last_query_type": last_context.get("query_type"),
        })

    examples = """
Examples:

User: dime si el dns ha ido bien hoy
JSON:
{"intent":"dns_summary","host":null,"hosts":[],"time_range":"today","metric_focus":"health","top_n":null,"domain":null,"query_type":null,"compare_mode":null,"confidence":0.92}

User: que host va peor de memoria ram
JSON:
{"intent":"ram_compare_hosts","host":null,"hosts":["raspberry","ASUS_Josemi"],"time_range":"now","metric_focus":"used_percent","top_n":null,"domain":null,"query_type":null,"compare_mode":"max","confidence":0.95}

User: dime el estado del trafico dns hoy
JSON:
{"intent":"dns_summary","host":null,"hosts":[],"time_range":"today","metric_focus":"traffic","top_n":null,"domain":null,"query_type":null,"compare_mode":null,"confidence":0.94}

User: cuantas consultas tuvo youtube.com hoy
JSON:
{"intent":"dns_domain_query_count","host":null,"hosts":[],"time_range":"today","metric_focus":null,"top_n":null,"domain":"youtube.com","query_type":null,"compare_mode":null,"confidence":0.98}

User: cual es la carga actual del pc
JSON:
{"intent":"cpu_status","host":"ASUS_Josemi","hosts":[],"time_range":"now","metric_focus":"load","top_n":null,"domain":null,"query_type":null,"compare_mode":null,"confidence":0.96}

User: cual es la carga actual del ordenador
JSON:
{"intent":"cpu_status","host":"ASUS_Josemi","hosts":[],"time_range":"now","metric_focus":"load","top_n":null,"domain":null,"query_type":null,"compare_mode":null,"confidence":0.96}

User: quien tiene mas carga, el pc o la raspberry
JSON:
{"intent":"cpu_compare_hosts","host":null,"hosts":["raspberry","ASUS_Josemi"],"time_range":"now","metric_focus":"load","top_n":null,"domain":null,"query_type":null,"compare_mode":"max","confidence":0.97}

User: y la raspberry?
Previous context:
{"last_intent":"host_status","last_host":"ASUS_Josemi","last_hosts":[],"last_time_range":"now","last_domain":null,"last_query_type":null}
JSON:
{"intent":"host_status","host":"raspberry","hosts":[],"time_range":"now","metric_focus":null,"top_n":null,"domain":null,"query_type":null,"compare_mode":null,"confidence":0.97}
""".strip()

    return f"""{SYSTEM_PROMPT}

Previous context:
{json.dumps(context_block, ensure_ascii=False)}

{examples}

User: {user_query}
JSON:
""".strip()


def _extract_json_from_text(text: str):
    # Try to parse the full response as JSON
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Fallback in case the model adds text around the JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        candidate = match.group(0)

        try:
            return json.loads(candidate)
        except Exception:
            return None

    return None


def _normalize_llm_result(data: dict) -> dict:
    # Validate and clean the fields returned by the LLM
    if not isinstance(data, dict):
        return {
            "intent": "unknown",
            "host": None,
            "hosts": [],
            "time_range": None,
            "metric_focus": None,
            "top_n": None,
            "domain": None,
            "query_type": None,
            "compare_mode": None,
            "confidence": None,
        }

    intent = data.get("intent", "unknown")

    if intent not in ALLOWED_INTENTS:
        intent = "unknown"

    host = data.get("host")

    if host not in {"raspberry", "ASUS_Josemi", None}:
        host = None

    hosts = data.get("hosts", [])

    if not isinstance(hosts, list):
        hosts = []

    hosts = [
        host_name
        for host_name in hosts
        if host_name in {"raspberry", "ASUS_Josemi"}
    ]

    hosts = list(dict.fromkeys(hosts))

    time_range = data.get("time_range")

    if not isinstance(time_range, str):
        time_range = None

    metric_focus = data.get("metric_focus")

    if not isinstance(metric_focus, str):
        metric_focus = None

    top_n = data.get("top_n")

    if not isinstance(top_n, int):
        top_n = None

    domain = data.get("domain")

    if not isinstance(domain, str):
        domain = None

    query_type = data.get("query_type")

    if not isinstance(query_type, str):
        query_type = None

    compare_mode = data.get("compare_mode")

    if compare_mode not in {"max", "min", None}:
        compare_mode = None

    confidence = data.get("confidence")

    if not isinstance(confidence, (int, float)):
        confidence = None

    return {
        "intent": intent,
        "host": host,
        "hosts": hosts,
        "time_range": time_range,
        "metric_focus": metric_focus,
        "top_n": top_n,
        "domain": domain,
        "query_type": query_type,
        "compare_mode": compare_mode,
        "confidence": confidence,
    }


def _postprocess(
    user_input: str,
    normalized: str,
    result: dict,
    last_context: Optional[dict] = None
) -> dict:
    # Adjust the LLM result using simple local rules
    intent = result["intent"]
    host = result["host"]
    hosts = result["hosts"]
    top_n = result["top_n"]
    domain = result.get("domain")
    query_type = result.get("query_type")
    compare_mode = result.get("compare_mode")
    comparison_style = result.get("comparison_style")

    detected_hosts = detect_all_hosts(normalized)

    single_host_intents = {
        "host_status",
        "cpu_status",
        "ram_status",
        "ram_used_pct",
        "ram_available",
        "disk_status",
        "disk_used_pct",
    }

    # Prefer the host explicitly mentioned by the user
    if intent in single_host_intents and len(detected_hosts) == 1:
        host = detected_hosts[0]
        hosts = []

    single_host_cpu_clues = [
        "carga",
        "cpu",
        "load",
        "cargado",
        "cargada",
    ]

    explicit_compare_clues = [
        "compara",
        "comparar",
        "frente a",
        "respecto a",
        "mas que",
        "menos que",
        "mayor que",
        "menor que",
        "que host",
        "cual host",
        "cual de los hosts",
        "quien tiene mas",
        "quien va mas",
        "ambos",
        "los dos",
    ]

    # Avoid turning a single-host CPU question into a comparison
    if (
        len(detected_hosts) == 1
        and any(clue in normalized for clue in single_host_cpu_clues)
        and not any(clue in normalized for clue in explicit_compare_clues)
    ):
        intent = "cpu_status"
        host = detected_hosts[0]
        hosts = []

    # Detect DNS summary requests that the model may classify too specifically
    if "dns" in normalized or "trafico dns" in normalized:
        if any(clue in normalized for clue in [
            "ha ido bien",
            "como ha ido",
            "que tal ha ido",
            "estado del trafico",
            "estado del trafico dns",
            "estado dns",
            "estado del dns",
            "resumen",
            "trafico dns",
        ]):
            intent = "dns_summary"

    # RAM comparisons
    if any(clue in normalized for clue in ["ram", "memoria"]):
        if any(clue in normalized for clue in [
            "que host",
            "quien",
            "cual",
            "compara",
            "comparar",
            "va peor",
            "va mejor",
            "mas",
            "menos",
        ]):
            intent = "ram_compare_hosts"
            host = None
            hosts = (
                detected_hosts
                if len(detected_hosts) >= 2
                else SUPPORTED_HOSTS[:]
            )

            if compare_mode is None:
                compare_mode = (
                    "min"
                    if "menos" in normalized or "mejor" in normalized
                    else "max"
                )

        if any(clue in normalized for clue in [
            "va peor",
            "peor de memoria",
            "peor de ram",
            "mas ahogado",
        ]):
            intent = "ram_compare_hosts"
            compare_mode = "max"
            comparison_style = "worst_best"

        elif any(clue in normalized for clue in [
            "va mejor",
            "mejor de memoria",
            "mejor de ram",
            "menos ocupado",
            "mas libre",
        ]):
            intent = "ram_compare_hosts"
            compare_mode = "min"
            comparison_style = "worst_best"

    # Disk comparisons
    if any(clue in normalized for clue in ["disco", "almacenamiento"]):
        if any(clue in normalized for clue in [
            "que host",
            "quien",
            "cual",
            "compara",
            "comparar",
            "va peor",
            "va mejor",
            "mas",
            "menos",
        ]):
            intent = "disk_compare_hosts"
            host = None
            hosts = (
                detected_hosts
                if len(detected_hosts) >= 2
                else SUPPORTED_HOSTS[:]
            )

            if compare_mode is None:
                compare_mode = (
                    "min"
                    if "menos" in normalized or "mejor" in normalized
                    else "max"
                )

    # CPU comparisons
    if any(clue in normalized for clue in [
        "cpu",
        "carga",
        "load",
        "cargado",
    ]):
        if any(clue in normalized for clue in [
            "que host",
            "quien",
            "cual",
            "compara",
            "comparar",
            "va peor",
            "va mejor",
            "mas",
            "menos",
        ]):
            intent = "cpu_compare_hosts"
            host = None
            hosts = (
                detected_hosts
                if len(detected_hosts) >= 2
                else SUPPORTED_HOSTS[:]
            )

            if compare_mode is None:
                compare_mode = (
                    "min"
                    if "menos" in normalized or "mejor" in normalized
                    else "max"
                )

    # Recover simple follow-up questions using the previous context
    if last_context and intent == "unknown":
        last_intent = last_context.get("intent")

        simple_follow_ups = {
            "y la raspberry",
            "y la raspi",
            "y el pc",
            "y el ordenador",
            "y el asus",
        }

        if normalized in simple_follow_ups and detected_hosts:
            host = detected_hosts[0]

            if last_intent in single_host_intents:
                intent = last_intent
            else:
                intent = "host_status"

    # DNS intents never use system hosts
    if intent.startswith("dns_"):
        host = None
        hosts = []

    # Fill the host when a single-host intent is detected
    if intent in single_host_intents:
        if host is None and len(detected_hosts) == 1:
            host = detected_hosts[0]
            hosts = []

    # Comparisons always work with a list of hosts
    if intent in {
        "ram_compare_hosts",
        "disk_compare_hosts",
        "cpu_compare_hosts",
    }:
        host = None

        if not hosts:
            hosts = SUPPORTED_HOSTS[:]

    # Set a default number of results for list-based DNS intents
    if (
        intent in {
            "dns_top_domains",
            "dns_top_clients",
            "dns_query_types_summary",
        }
        and top_n is None
    ):
        top_n = detect_top_n(normalized, default=5)

    # DNS queries use a historical range, while system metrics use current data
    default_time = "-6h" if intent.startswith("dns_") else "now"
    time_range = detect_dynamic_time_range(
        normalized,
        default=default_time
    )

    if intent == "unknown":
        return _safe_fallback(
            user_input,
            normalized,
            host=host,
            hosts=hosts
        )

    return {
        "ok": True,
        "intent": intent,
        "host": host,
        "hosts": hosts,
        "time_range": time_range,
        "top_n": top_n,
        "domain": domain,
        "query_type": query_type,
        "compare_mode": compare_mode,
        "comparison_style": comparison_style,
        "raw_text": user_input,
        "normalized_text": normalized,
        "used_context": bool(last_context),
    }


def _rule_based_llm_precheck(
    user_input: str,
    normalized: str
) -> Optional[dict]:
    # Handle simple system queries before calling the LLM
    detected_hosts = detect_all_hosts(normalized)

    host_status_clues = [
        "como ves",
        "que tal esta",
        "que tal esta el",
        "que tal va",
        "va bien",
        "funciona correctamente",
        "funciona bien",
        "estado del",
        "estado de la",
        "como esta",
    ]

    if len(detected_hosts) == 1:
        if any(clue in normalized for clue in host_status_clues):
            return {
                "ok": True,
                "intent": "host_status",
                "host": detected_hosts[0],
                "hosts": [],
                "time_range": "now",
                "top_n": None,
                "raw_text": user_input,
                "normalized_text": normalized,
                "used_context": False,
            }

    both_hosts_clues = [
        "como se encuentran los hosts",
        "como estan los hosts",
        "como estan ambos hosts",
        "estado de los hosts",
        "estado de ambos hosts",
        "dime el estado de los dos",
        "como estan el pc y la raspberry",
        "como estan ambos",
    ]

    if any(clue in normalized for clue in both_hosts_clues):
        return {
            "ok": True,
            "intent": "hosts_status",
            "host": None,
            "hosts": SUPPORTED_HOSTS[:],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    cpu_status_clues = [
        "como de cargado va",
        "que carga tiene",
        "que load tiene",
        "como va de cpu",
        "como va de carga",
        "esta muy cargado",
    ]

    if len(detected_hosts) == 1:
        if any(clue in normalized for clue in cpu_status_clues):
            return {
                "ok": True,
                "intent": "cpu_status",
                "host": detected_hosts[0],
                "hosts": [],
                "time_range": "now",
                "top_n": None,
                "raw_text": user_input,
                "normalized_text": normalized,
                "used_context": False,
            }

    cpu_compare_markers = [
        "que host tiene mas carga",
        "quien tiene mas carga",
        "quien va mas cargado",
        "cual de los hosts va mas cargado",
        "cual host va mas cargado",
        "que host va mas cargado",
        "compara la carga",
        "comparar la carga",
        "mayor load",
        "mas carga ahora",
        "que host tiene mayor load",
        "que host va peor de carga",
        "cual de los hosts tiene mayor load",
    ]

    if any(marker in normalized for marker in cpu_compare_markers):
        return {
            "ok": True,
            "intent": "cpu_compare_hosts",
            "host": None,
            "hosts": SUPPORTED_HOSTS[:],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    comparison_words = [
        "que host",
        "cual host",
        "cual de los hosts",
        "quien",
        "compara",
        "comparar",
    ]

    cpu_words = [
        "carga",
        "cargado",
        "load",
    ]

    if (
        any(word in normalized for word in comparison_words)
        and any(word in normalized for word in cpu_words)
    ):
        return {
            "ok": True,
            "intent": "cpu_compare_hosts",
            "host": None,
            "hosts": SUPPORTED_HOSTS[:],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    return None


def parse_user_query_with_llm(
    user_input: str,
    last_context: Optional[dict] = None
) -> dict:
    # Normalize the query and detect any hosts mentioned by the user
    normalized = normalize_text(user_input)
    detected_hosts = detect_all_hosts(normalized)

    # Try simple local rules before sending the query to Ollama
    prechecked = _rule_based_llm_precheck(
        user_input,
        normalized
    )

    if prechecked is not None:
        return prechecked

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_prompt(
            user_input,
            last_context=last_context
        ),
        "stream": False,
        "format": "json",
        "keep_alive": "10m",
    }

    try:
        # Ask the local model to classify the query
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=90
        )
        response.raise_for_status()

        data = response.json()
        raw_text = data.get("response", "").strip()

        parsed = _extract_json_from_text(raw_text)

        if parsed is None:
            return _safe_fallback(
                user_input,
                normalized,
                host=detected_hosts[0] if detected_hosts else None,
                hosts=detected_hosts,
            )

        normalized_result = _normalize_llm_result(parsed)

        return _postprocess(
            user_input,
            normalized,
            normalized_result,
            last_context=last_context
        )

    except Exception as e:
        # Return a controlled error if the local LLM is not available
        return {
            "ok": False,
            "intent": None,
            "host": detected_hosts[0] if detected_hosts else None,
            "hosts": detected_hosts,
            "time_range": None,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "error": f"Fallo en router LLM: {e}",
        }