import re
import unicodedata
from typing import Optional


# Host aliases accepted by the parser
HOST_ALIASES = {
    "raspberry": "raspberry",
    "raspi": "raspberry",
    "rpi": "raspberry",
    "pc": "ASUS_Josemi",
    "asus": "ASUS_Josemi",
    "asus_josemi": "ASUS_Josemi",
    "ordenador": "ASUS_Josemi",
}


# General system status patterns
STATUS_PATTERNS = [
    "como esta",
    "que tal esta",
    "estado",
    "resumen",
    "como va",
    "situacion",
    "esta bien",
    "va bien",
    "que le pasa",
    "que pasa con",
    "como sigue",
    "todo bien",
    "funciona bien",
    "funciona correctamente",
    "esta funcionando bien",
    "esta funcionando correctamente",
    "todo correcto con",
    "como se encuentra",
    "como se encuentra el",
    "como se encuentra la",
    "se encuentra bien",
]


# CPU-related patterns
CPU_COMPARE_PATTERNS = [
    "que host tiene mas carga",
    "cual tiene mas carga",
    "quien tiene mas carga",
    "quien va mas cargado",
    "compara la carga",
    "comparar la carga",
    "mayor load",
    "mas carga ahora",
    "que host va mas cargado",
]

CPU_STATUS_PATTERNS = [
    "como de cargado va",
    "como de cargada va",
    "que carga tiene",
    "que load tiene",
    "como va de cpu",
    "como va de carga",
    "esta muy cargado",
    "cual es la carga actual",
    "cual es su carga actual",
    "dime la carga actual",
    "carga actual",
    "load actual",
    "nivel de carga actual",
    "uso actual de cpu",
    "estado actual de la cpu",
]


# DNS domain and client patterns
DNS_TOP_DOMAINS_PATTERNS = [
    "que dominio ha sido el mas consultado",
    "cual ha sido el dominio mas consultado",
    "dominio mas consultado",
    "top dominios",
    "top domain",
    "top domains",
    "dominios mas consultados",
    "lista de dominios",
    "sacame una lista de dominios",
    "dime los dominios mas consultados",
    "dominios mas usados",
    "top de dominios",
    "top de dominio",
    "sacame el top",
]

DNS_TOP_CLIENTS_PATTERNS = [
    "que cliente ha hecho mas consultas",
    "que cliente ha sido el mas activo",
    "que cliente ha generado mas trafico dns",
    "que ip ha generado mas trafico dns",
    "cliente mas activo",
    "clientes mas activos",
    "top clientes",
    "top clientes activos",
    "lista de clientes",
    "lista de clientes activos",
    "sacame una lista de los clientes activos",
    "dime los clientes mas activos",
    "clientes activos",
]

DNS_ACTIVE_CLIENTS_PATTERNS = [
    "que clientes han estado activos",
    "lista de clientes activos",
    "clientes activos",
    "clientes con actividad",
    "que ips han tenido actividad dns",
    "que clientes han tenido actividad dns",
    "dame los clientes activos",
    "sacame una lista de clientes activos",
    "dame las ips de los clientes activos",
    "dame informacion de los clientes activos",
    "muestrame los clientes activos",
    "muestrame las ips de los clientes activos",
    "sacame las ips de los clientes activos",
]


# DNS summary and metric patterns
DNS_SUMMARY_PATTERNS = [
    "resumen del dns",
    "hazme un resumen del dns",
    "resume la actividad dns",
    "resumen del trafico dns",
    "como ha estado el trafico dns",
    "estado dns",
    "estado del dns",
    "cual es el estado del dns",
    "dime el estado del dns",
    "que tal esta la red",
    "como esta la red",
    "como va la red",
    "estado de la red",
    "dime el estado de la red",
    "resumen de la red",
    "como ha ido la red",
    "que tal va la red",
    "esta funcionando bien la red",
    "funciona bien la red",
    "que pasa con la red",
    "que le pasa a la red",
    "que tal va internet",
    "como va internet",
    "como esta internet",
    "estado de internet",
    "como va el dns",
    "como esta el dns",
    "que tal esta el dns",
]

DNS_TOTAL_QUERIES_PATTERNS = [
    "cuantas consultas dns ha habido",
    "cuantas consultas ha habido",
    "numero de consultas dns",
    "total de consultas dns",
    "cuantas peticiones dns ha habido",
    "consultas dns que han habido",
]

DNS_QPS_PATTERNS = [
    "cual ha sido el qps medio",
    "qps medio",
    "tasa media de consultas dns",
    "media de consultas por segundo",
    "dns query rate",
    "qps",
    "qps promedio",
    "media de qps",
]

DNS_BLOCKED_PCT_PATTERNS = [
    "que porcentaje se ha bloqueado",
    "porcentaje bloqueado",
    "cuanto se ha bloqueado",
    "blocked percentage",
    "porcentaje del trafico bloqueado",
    "consultas bloqueadas",
    "ha sido bloqueado",
]

DNS_CACHED_PCT_PATTERNS = [
    "cuanto ha resuelto la cache",
    "que porcentaje ha resuelto la cache",
    "porcentaje en cache",
    "cached percentage",
    "cuanto se ha servido desde cache",
    "resuelto por cache",
    "resuelto desde cache",
    "trafico cacheado",
    "se ha cacheado",
    "cuanto trafico ha sido cacheado",
    "cuanto trafico fue cacheado",
    "cuanto trafico ha resuelto la cache",
    "cuanto trafico resolvio la cache",
    "cuanto trafico se resolvio desde cache",
    "que parte del trafico fue cacheada",
    "que parte del trafico ha sido cacheada",
    "que porcentaje del trafico fue cacheado",
    "que porcentaje del trafico ha sido cacheado",
]

DNS_ACTIVE_CLIENTS_COUNT_PATTERNS = [
    "cuantos clientes activos se han detectado",
    "cuantos clientes activos ha habido",
    "numero de clientes activos",
    "clientes activos detectados",
    "cuantos clientes hay activos",
    "cuantos clientes activos hay",
    "cuantos clientes hay ahora activos",
    "clientes activos hay",
    "clientes han habido activos",
]


# DNS query type patterns
DNS_QUERY_TYPES_PATTERNS = [
    "que tipo dns predomina",
    "cual es el tipo de consulta mas frecuente",
    "cual es el tipo dns mas frecuente",
    "distribucion de tipos dns",
    "distribucion de consultas dns",
    "resume los tipos dns",
    "resume los tipos de consulta",
    "resume los tipos de trafico dns",
    "top tipos dns",
    "tipos dns",
    "tipos de consulta dns",
    "que tipos de consulta ha habido",
    "que tipos dns ha habido",
    "distribucion del trafico dns",
    "tipos de trafico dns",
    "tipo de trafico dns",
]


# Forwarded and cached query patterns
DNS_FORWARDED_VS_CACHED_PATTERNS = [
    "forwarded vs cached",
    "cached vs forwarded",
    "que ha predominado forwarded o cached",
    "que ha predominado cache o forwarded",
    "como se reparte forwarded frente a cache",
    "como se reparte cache frente a forwarded",
    "comparame forwarded y cached",
    "comparacion entre forwarded y cached",
    "comparacion entre cache y forwarded",
    "compara forwarded y cached",
    "compara cached y forwarded",
    "compara cacheado contra enviado",
    "que ha predominado el trafico cacheado o el reenviado",
    "que ha predominado entre cacheado y reenviado",
    "que ha predominado entre el cacheado y el reenviado",
    "dime la distribucion del trafico cacheado vs el reenviado",
    "distribucion del trafico cacheado vs el reenviado",
    "distribucion del trafico reenviado vs cacheado",
    "trafico cacheado vs reenviado",
    "trafico reenviado vs cacheado",
    "cacheado vs reenviado",
    "reenviado vs cacheado",
    "cacheado o reenviado",
    "reenvio vs cache",
    "cache vs reenvio",
]

DNS_FORWARDED_COUNT_PATTERNS = [
    "cuantas consultas se han reenviado",
    "cuantas consultas han sido reenviadas",
    "cuanto ha ido a forwarded",
    "cuantas consultas forwarded ha habido",
    "total forwarded",
    "consultas reenviadas",
]

DNS_CACHED_COUNT_PATTERNS = [
    "cuantas consultas se han resuelto desde cache",
    "cuantas consultas han salido de cache",
    "cuanto ha ido a cache",
    "cuantas consultas cached ha habido",
    "total cached",
    "consultas resueltas desde cache",
]


# RAM-related patterns
RAM_COMPARE_PATTERNS = [
    "compara la ram",
    "compara la memoria",
    "que host usa mas memoria",
    "quien tiene la ram mas ocupada",
    "cual tiene mas ram usada",
    "quien usa mas ram",
    "quien usa mas memoria",
]

RAM_AVAILABLE_PATTERNS = [
    "cuanta ram libre tiene",
    "cuanta memoria libre tiene",
    "ram disponible",
    "memoria disponible",
    "cuanta ram queda libre",
    "cuanta memoria queda libre",
]

RAM_USED_PCT_PATTERNS = [
    "que porcentaje de ram usa",
    "que porcentaje de memoria usa",
    "cuanta ram usa",
    "cuanta memoria usa",
    "ram usada",
    "memoria usada",
]

RAM_STATUS_PATTERNS = [
    "cuanta ram usa",
    "cuanta ram tiene usada",
    "como esta la memoria",
    "estado de la ram",
    "estado de la memoria",
    "que porcentaje de ram usa",
    "cuanta ram libre tiene",
    "cuanta memoria libre tiene",
    "ram del",
    "memoria del",
]


# Disk-related patterns
DISK_COMPARE_PATTERNS = [
    "compara el disco",
    "compara el almacenamiento",
    "que host tiene el disco mas ocupado",
    "quien tiene el disco mas ocupado",
    "cual tiene mas disco usado",
    "quien tiene mas almacenamiento usado",
]

DISK_USED_PCT_PATTERNS = [
    "que porcentaje de disco usa",
    "que porcentaje de almacenamiento usa",
    "cuanto disco tiene ocupado",
    "disco usado",
    "almacenamiento usado",
]

DISK_STATUS_PATTERNS = [
    "como esta el disco",
    "estado del disco",
    "estado del almacenamiento",
    "disco del",
    "almacenamiento del",
]


# Multi-host status patterns
HOSTS_STATUS_PATTERNS = [
    "como se encuentran los hosts",
    "como estan los hosts",
    "como estan ambos hosts",
    "estado de los hosts",
    "estado de ambos hosts",
    "dime el estado de los dos",
    "como estan el pc y la raspberry",
    "como estan ambos",
]


SUPPORTED_HOSTS = ["raspberry", "ASUS_Josemi"]

def strip_request_prefix(text: str) -> str:
    # Remove common request expressions that do not affect the intent
    request_prefixes = [
        "dame ",
        "dime ",
        "muestrame ",
        "sacame ",
        "quiero ver ",
        "quiero saber ",
        "podrias decirme ",
        "puedes decirme ",
        "me puedes decir ",
        "me podrias decir ",
        "dime rapidamente ",
        "dime rapido ",
    ]

    for prefix in request_prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()

    return text


def normalize_text(text: str) -> str:
    # Normalize the user input before applying the parser rules
    text = text.lower().strip()

    # Remove accents
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    # Replace some common abbreviations
    text = re.sub(r"\bq\b", "que", text)
    text = re.sub(r"\bqu\b", "que", text)
    text = re.sub(r"\bpa\b", "para", text)
    text = re.sub(r"\bms\b", "mas", text)

    # Remove punctuation and extra spaces
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    text = strip_request_prefix(text)

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


def detect_host(text: str):
    # Return the first host detected in the query
    hosts = detect_all_hosts(text)

    if hosts:
        return hosts[0]

    return None


def detect_compare_mode(text: str) -> str:
    # Decide whether the comparison looks for the highest or lowest value
    if "menos" in text:
        return "min"

    return "max"


def detect_disk_compare_mode(text: str) -> str:
    # Disk comparisons need special handling when the user asks about free space
    free_space_clues = [
        "libre",
        "espacio libre",
        "almacenamiento libre",
        "disco libre",
        "mas espacio",
        "menos espacio",
    ]

    is_free_space_question = any(
        clue in text for clue in free_space_clues
    )

    if is_free_space_question:
        if "mas" in text:
            return "min"

        if "menos" in text:
            return "max"

    if "menos" in text:
        return "min"

    return "max"


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

    # Expressions referring to the current moment
    if any(x in text for x in [
        "ahora mismo",
        "ahora",
        "actualmente",
        "actual",
        "en este momento",
        "en este instante",
    ]):
        return "-5m"

    # Queries referring to the current day
    if any(x in text for x in [
        "de hoy",
        "hoy",
        "del dia",
        "durante el dia",
    ]):
        return "today"

    # Common expressions that do not follow a numeric pattern
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

    # Numeric time expressions such as "last 3 hours" or "2 days ago"
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

    # Compact expressions such as "3h", "2d" or "1w"
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
    # Detect how many results the user wants to see
    patterns = [
        r"\btop\s+(\d+)\b",
        r"\blista\s+de\s+(\d+)\b",
        r"\blista\s+de\s+los\s+(\d+)\b",
        r"\bsacame\s+el\s+top\s+(\d+)\b",
        r"\bdame\s+los\s+(\d+)\s+dominios?\b",
        r"\bdime\s+los\s+(\d+)\s+dominios?\b",
        r"\bquiero\s+una\s+lista\s+de\s+(\d+)\b",
        r"\bquiero\s+una\s+lista\s+de\s+los\s+(\d+)\b",
        r"\bcuales?\s+son\s+los\s+(\d+)\s+dominios?\b",
        r"\b(\d+)\s+dominios?\s+mas\s+consultados\b",
        r"\b(\d+)\s+dominios?\s+mas\s+usados\b",
        r"\blos\s+(\d+)\s+mas\s+consultados\b",

        r"\bdame\s+los\s+(\d+)\s+clientes?\b",
        r"\bdime\s+los\s+(\d+)\s+clientes?\b",
        r"\blista\s+de\s+los\s+(\d+)\s+clientes?\b",
        r"\buna\s+lista\s+de\s+los\s+(\d+)\s+clientes?\b",
        r"\bcuales?\s+son\s+los\s+(\d+)\s+clientes?\b",
        r"\b(\d+)\s+clientes?\s+mas\s+activos\b",
        r"\b(\d+)\s+clientes?\s+mas\s+frecuentes\b",
        r"\b(\d+)\s+clientes?\s+con\s+mas\s+consultas\b",
        r"\blos\s+(\d+)\s+clientes?\s+mas\s+activos\b",
        r"\blos\s+(\d+)\s+clientes?\s+mas\s+frecuentes\b",
        r"\blos\s+(\d+)\s+clientes?\s+con\s+mas\s+consultas\b",
        r"\btop\s+(\d+)\s+clientes?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            # Limit the requested list to a maximum of 50 results
            return max(1, min(int(match.group(1)), 50))

    # If the user asks for a generic list, return a small default list
    generic_list_clues = [
        "lista de dominios",
        "sacame una lista de dominios",
        "dime los dominios mas consultados",
        "dominios mas consultados",
        "dominios mas usados",
        "top dominios",

        "lista de clientes",
        "dame una lista de clientes",
        "dime los clientes mas activos",
        "clientes mas activos",
        "clientes mas frecuentes",
        "clientes con mas consultas",
        "top clientes",
    ]

    if any(clue in text for clue in generic_list_clues):
        return 5

    return default


def extract_domain_from_query(text: str) -> Optional[str]:
    # Try to extract a domain from common query expressions
    match = re.search(
        r"\b(?:dominio\s+de|dominio|sobre|ha\s+tenido|se\s+ha\s+consultado|se\s+ha\s+hecho\s+al\s+dominio\s+de)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
        text
    )

    if match:
        return match.group(1).lower()

    # Fallback to any domain-like expression found in the query
    match = re.search(
        r"\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
        text
    )

    if match:
        return match.group(1).lower()

    return None


def extract_query_type_from_query(text: str) -> Optional[str]:
    # Detect DNS query types mentioned by the user
    text_upper = text.upper()

    type_aliases = {
        "IPV4": "A",
        "IPV6": "AAAA",
    }

    for alias, real_type in type_aliases.items():
        if re.search(rf"\b{alias}\b", text_upper):
            return real_type

    supported_types = [
        "AAAA",
        "HTTPS",
        "NAPTR",
        "SVCB",
        "PTR",
        "TXT",
        "SRV",
        "A",
    ]

    for dns_type in supported_types:
        if re.search(rf"\b{dns_type}\b", text_upper):
            return dns_type

    return None


def detect_is_client_list_request(text: str) -> bool:
    # Check whether the query refers to DNS clients
    client_clues = [
        "cliente",
        "clientes",
        "ip",
        "ips",
    ]

    return any(clue in text for clue in client_clues)


def detect_is_active_clients_request(text: str) -> bool:
    # Detect requests asking specifically for active clients
    active_client_clues = [
        "clientes activos",
        "clientes con actividad",
        "han estado activos",
        "han tenido actividad dns",
        "ips activas",
        "ips con actividad",
        "ips de los clientes activos",
        "clientes activos hace",
        "que clientes estan activos",
        "que clientes han estado activos",
        "cuales son los clientes activos",
        "cuales son esos clientes",
        "esos clientes que estan activos",
    ]

    request_verbs = [
        "dame",
        "dime",
        "muestrame",
        "sacame",
        "quiero ver",
        "cuales son",
        "que clientes",
    ]

    if any(clue in text for clue in active_client_clues):
        return True

    if any(verb in text for verb in request_verbs):
        if "clientes" in text and "ips" in text:
            return True

        if "clientes" in text and (
            "activo" in text
            or "actividad" in text
        ):
            return True

    return False


def detect_explicit_intent(
    text: str,
    host: Optional[str],
    hosts: list,
    original_text: Optional[str] = None
):
    # Detect status and CPU-related intents
    for pattern in HOSTS_STATUS_PATTERNS:
        if pattern in text:
            return "hosts_status"

    for pattern in CPU_STATUS_PATTERNS:
        if pattern in text and host:
            return "cpu_status"

    for pattern in CPU_COMPARE_PATTERNS:
        if pattern in text:
            return "cpu_compare_hosts"

    # Detect DNS query type intents
    for pattern in DNS_QUERY_TYPES_PATTERNS:
        if pattern in text:
            return "dns_query_types_summary"

    query_type = extract_query_type_from_query(
        original_text if original_text else text
    )

    if query_type:
        if (
            "cuantas consultas" in text
            or "cuantas veces" in text
            or "cuanto trafico" in text
            or "cuanto ha habido" in text
            or "consultas ha habido" in text
        ):
            return "dns_query_type_count"

    if (
        "tipo dns" in text
        or "tipos dns" in text
        or "tipo de consulta" in text
        or "tipos de consulta" in text
        or "que tipo dns" in text
        or "que tipos de consulta" in text
        or "distribucion de tipos" in text
        or "distribucion del trafico dns" in text
        or "tipos del trafico dns" in text
        or "tipo de trafico dns" in text
        or "tipos de trafico dns" in text
    ):
        return "dns_query_types_summary"

    # Detect DNS summary requests
    for pattern in DNS_SUMMARY_PATTERNS:
        if pattern in text:
            return "dns_summary"

    if "dns" in text:
        if (
            "resumen" in text
            or "resume" in text
            or "actividad dns" in text
            or "resumen del trafico dns" in text
            or "como ha estado el trafico dns" in text
            or "estado del dns" in text
            or "estado dns" in text
            or "como ha estado" in text
            or "como va" in text
            or "que tal ha ido" in text
            or "como ha ido" in text
        ):
            return "dns_summary"

    # Detect total DNS query requests
    for pattern in DNS_TOTAL_QUERIES_PATTERNS:
        if pattern in text:
            return "dns_total_queries"

    if "dns" in text or "consultas dns" in text:
        if (
            "cuantas consultas" in text
            or "numero de consultas" in text
            or "total de consultas" in text
            or "consultas que han habido" in text
            or "consultas ha habido" in text
        ):
            return "dns_total_queries"

    # Detect QPS requests
    for pattern in DNS_QPS_PATTERNS:
        if pattern in text:
            return "dns_qps"

    if "qps" in text:
        return "dns_qps"

    # Detect blocked traffic requests
    for pattern in DNS_BLOCKED_PCT_PATTERNS:
        if pattern in text:
            return "dns_blocked_pct"

    if "bloquead" in text:
        if (
            "porcentaje" in text
            or "trafico" in text
            or "consultas" in text
        ):
            return "dns_blocked_pct"

    # Detect forwarded query count
    if (
        "forwarded" in text
        or "reenviado" in text
        or "reenviadas" in text
        or "reenviados" in text
    ):
        if (
            "cuantas consultas" in text
            or "cuantas" in text
            or "total" in text
            or "numero" in text
        ):
            return "dns_forwarded_count"

    # Detect forwarded vs cached comparisons
    for pattern in DNS_FORWARDED_VS_CACHED_PATTERNS:
        if pattern in text:
            return "dns_forwarded_vs_cached_summary"

    if (
        (
            "cache" in text
            or "cacheado" in text
            or "cacheada" in text
            or "cached" in text
        )
        and
        (
            "forwarded" in text
            or "reenviado" in text
            or "reenviada" in text
            or "reenviadas" in text
            or "reenviados" in text
        )
    ):
        return "dns_forwarded_vs_cached_summary"

    for pattern in DNS_FORWARDED_COUNT_PATTERNS:
        if pattern in text:
            return "dns_forwarded_count"

    # Detect cached query count
    if (
        "cache" in text
        or "cacheado" in text
        or "cacheada" in text
        or "cacheadas" in text
        or "cached" in text
    ):
        if (
            "cuantas consultas" in text
            or "cuantas" in text
            or "total" in text
            or "numero" in text
            or "consultas cacheadas" in text
            or "consultas resueltas desde cache" in text
        ):
            return "dns_cached_count"

    for pattern in DNS_CACHED_COUNT_PATTERNS:
        if pattern in text:
            return "dns_cached_count"

    # Detect cached traffic percentage
    for pattern in DNS_CACHED_PCT_PATTERNS:
        if pattern in text:
            return "dns_cached_pct"

    if (
        "cache" in text
        or "cacheado" in text
        or "cacheada" in text
        or "cacheadas" in text
        or "cached" in text
    ):
        if (
            "trafico" in text
            or "porcentaje" in text
            or "que porcentaje" in text
            or "cuanto porcentaje" in text
            or "que parte" in text
            or "cuanto ha sido" in text
            or "cuanto fue" in text
        ):
            return "dns_cached_pct"

    # Detect active client count
    for pattern in DNS_ACTIVE_CLIENTS_COUNT_PATTERNS:
        if pattern in text:
            return "dns_active_clients_count"

    if (
        ("cliente" in text or "clientes" in text)
        and "activo" in text
    ):
        if (
            "cuanto" in text
            or "cuantos" in text
            or "numero" in text
            or "hay" in text
            or "han habido" in text
        ):
            return "dns_active_clients_count"

    # Detect active client lists
    for pattern in DNS_ACTIVE_CLIENTS_PATTERNS:
        if pattern in text:
            return "dns_active_clients_list"

    if detect_is_active_clients_request(text):
        return "dns_active_clients_list"

    # Detect generic DNS query type requests
    if ("tipo" in text or "tipos" in text) and (
        "dns" in text
        or "trafico" in text
        or "consulta" in text
        or "consultas" in text
    ):
        return "dns_query_types_summary"

    # Detect top DNS clients
    for pattern in DNS_TOP_CLIENTS_PATTERNS:
        if pattern in text:
            return "dns_top_clients"

    if "cliente" in text or "clientes" in text:
        if (
            "mas activo" in text
            or "mas activos" in text
            or "mas consultas" in text
            or "frecuente" in text
            or "frecuentes" in text
            or "top clientes" in text
        ):
            return "dns_top_clients"

    if detect_is_client_list_request(text) and (
        "consultas" in text
        or "trafico dns" in text
        or "top" in text
        or "mas activo" in text
        or "mas activos" in text
    ):
        return "dns_top_clients"

    # Detect top DNS domains
    for pattern in DNS_TOP_DOMAINS_PATTERNS:
        if pattern in text:
            return "dns_top_domains"

    domain_source = original_text.lower() if original_text else text
    domain = extract_domain_from_query(domain_source)

    if domain:
        if (
            "cuantas consultas" in text
            or "cuantas veces" in text
            or "cuanto se ha consultado" in text
            or "cuantas consultas ha tenido" in text
            or "consultas ha tenido" in text
            or "se han hecho al dominio" in text
        ):
            return "dns_domain_query_count"

    dns_keywords = [
        "dominios",
        "top",
        "consultados",
        "usados",
    ]

    if any(word in text for word in dns_keywords):
        if "dominios" in text:
            return "dns_top_domains"

        if "top" in text and (
            "consultados" in text
            or "usados" in text
        ):
            return "dns_top_domains"

        if "top" in text and re.search(r"\btop\s+\d+\b", text):
            return "dns_top_domains"

    # Detect disk-related intents
    for pattern in DISK_COMPARE_PATTERNS:
        if pattern in text:
            return "disk_compare_hosts"

    if "disco" in text or "almacenamiento" in text:
        if (
            "compara" in text
            or "comparar" in text
            or "ambos" in text
            or "dos" in text
            or "hosts" in text
            or "dispositivos" in text
            or "quien" in text
            or "cual" in text
            or "mas" in text
            or "menos" in text
        ):
            return "disk_compare_hosts"

    for pattern in DISK_USED_PCT_PATTERNS:
        if pattern in text and host:
            return "disk_used_pct"

    for pattern in DISK_STATUS_PATTERNS:
        if pattern in text and host:
            return "disk_status"

    if host and ("disco" in text or "almacenamiento" in text):
        if (
            "porcentaje" in text
            or "usa" in text
            or "usado" in text
            or "ocupado" in text
            or "ocupacion" in text
            or "utiliza" in text
        ):
            return "disk_used_pct"

        if (
            "estado" in text
            or "como esta" in text
            or "como va" in text
            or "que tal va" in text
        ):
            return "disk_status"

    # Detect RAM-related intents
    for pattern in RAM_COMPARE_PATTERNS:
        if pattern in text:
            return "ram_compare_hosts"

    if "ram" in text or "memoria" in text:
        if (
            "compara" in text
            or "comparar" in text
            or "ambos" in text
            or "dos" in text
            or "hosts" in text
            or "dispositivos" in text
            or "quien" in text
            or "cual" in text
            or "mas" in text
            or "menos" in text
        ):
            return "ram_compare_hosts"

        if (
            "como van de ram" in text
            or "como van de memoria" in text
        ):
            return "ram_compare_hosts"

    for pattern in RAM_AVAILABLE_PATTERNS:
        if pattern in text and host:
            return "ram_available"

    for pattern in RAM_USED_PCT_PATTERNS:
        if pattern in text and host:
            return "ram_used_pct"

    for pattern in RAM_STATUS_PATTERNS:
        if pattern in text and host:
            return "ram_status"

    if host and ("ram" in text or "memoria" in text):
        if (
            "libre" in text
            or "disponible" in text
            or "disponibles" in text
        ):
            return "ram_available"

        if (
            "usa" in text
            or "usada" in text
            or "uso" in text
            or "ocupacion" in text
            or "ocupada" in text
            or "utiliza" in text
            or "utilizado" in text
            or "porcentaje" in text
        ):
            return "ram_used_pct"

        if (
            "estado" in text
            or "como va" in text
            or "como esta" in text
            or "que tal va" in text
        ):
            return "ram_status"

    # Detect general host status
    if host:
        for pattern in STATUS_PATTERNS:
            if pattern in text:
                return "host_status"

        if (
            ("funciona" in text or "funcionando" in text)
            and
            (
                "bien" in text
                or "correctamente" in text
                or "correcto" in text
            )
        ):
            return "host_status"

    # Detect CPU status when the host is already known
    if host and (
        "carga" in text
        or "cargado" in text
        or "cpu" in text
        or "load" in text
    ):
        if (
            "como de" in text
            or "que" in text
            or "cual" in text
            or "como va" in text
            or "esta muy" in text
            or "actual" in text
            or "nivel" in text
        ):
            return "cpu_status"

    return None


def is_follow_up_query(text: str, host: Optional[str]):
    # Check whether the query is a short follow-up about a known host
    if not host:
        return False

    text = text.strip()

    follow_up_prefixes = [
        "y ",
        "y el ",
        "y la ",
        "y el de ",
        "y la de ",
        "y el del ",
        "y la del ",
    ]

    if not any(text.startswith(prefix) for prefix in follow_up_prefixes):
        return False

    words = text.split()

    if len(words) <= 6:
        return True

    return False


def is_cpu_follow_up_query(text: str, host: Optional[str]) -> bool:
    # Detect short follow-up questions related to CPU load
    if not host:
        return False

    cpu_clues = [
        "carga",
        "cargado",
        "cargada",
        "cpu",
        "load",
    ]

    return text.startswith("y ") and any(
        clue in text for clue in cpu_clues
    )


def extract_forwarded_cached_mode(text: str) -> Optional[str]:
    # Detect whether the user refers to forwarded or cached queries
    if (
        "forwarded" in text
        or "reenviado" in text
        or "reenviadas" in text
        or "reenviados" in text
    ):
        return "forwarded"

    if (
        "cache" in text
        or "cacheado" in text
        or "cacheada" in text
        or "cacheadas" in text
        or "cached" in text
    ):
        return "cached"

    return None


def is_forwarded_cached_follow_up(text: str) -> bool:
    # Detect follow-up questions about forwarded or cached queries
    text = text.strip()

    if not text.startswith("y"):
        return False

    return extract_forwarded_cached_mode(text) is not None


def is_dns_query_type_follow_up(text: str) -> bool:
    # Detect follow-up questions about a specific DNS query type
    text = text.strip()

    follow_up_prefixes = [
        "y ",
        "y de tipo ",
        "y tipo ",
        "y cuantas ",
        "y cuantas consultas ",
    ]

    if not any(text.startswith(prefix) for prefix in follow_up_prefixes):
        return False

    return extract_query_type_from_query(text) is not None


def is_dns_domain_follow_up(text: str) -> bool:
    # Detect follow-up questions about a specific domain
    text = text.lower().strip()

    follow_up_prefixes = [
        "y ",
        "y el ",
        "y la ",
        "y el dominio ",
        "y la web ",
        "y al dominio ",
    ]

    if not any(text.startswith(prefix) for prefix in follow_up_prefixes):
        return False

    return extract_domain_from_query(text) is not None


def parse_user_query(user_input: str, last_context: Optional[dict] = None) -> dict:
    # Normalize the input and detect the basic elements of the query
    normalized = normalize_text(user_input)
    original_text = user_input.lower()

    hosts = detect_all_hosts(normalized)
    host = hosts[0] if hosts else None

    intent = detect_explicit_intent(
        normalized,
        host,
        hosts,
        original_text=original_text
    )

    # Keep the previous time range when the user asks about another domain
    if last_context:
        last_intent = last_context.get("intent")

        if (
            last_intent == "dns_domain_query_count"
            and is_dns_domain_follow_up(original_text)
        ):
            domain = extract_domain_from_query(original_text)
            time_range = last_context.get("time_range", "-6h")

            return {
                "ok": True,
                "intent": "dns_domain_query_count",
                "host": None,
                "hosts": [],
                "domain": domain,
                "time_range": time_range,
                "top_n": None,
                "raw_text": user_input,
                "normalized_text": normalized,
                "used_context": True,
            }

    # DNS summary
    if intent == "dns_summary":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        return {
            "ok": True,
            "intent": "dns_summary",
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Simple DNS metrics
    if intent in [
        "dns_total_queries",
        "dns_qps",
        "dns_blocked_pct",
        "dns_cached_pct",
        "dns_active_clients_count",
    ]:
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        return {
            "ok": True,
            "intent": intent,
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Forwarded and cached DNS metrics
    if intent in [
        "dns_forwarded_vs_cached_summary",
        "dns_forwarded_count",
        "dns_cached_count",
    ]:
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        return {
            "ok": True,
            "intent": intent,
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # DNS query type summary
    if intent == "dns_query_types_summary":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        top_n = detect_top_n(normalized, default=3)
        full_distribution = False

        full_distribution_clues = [
            "distribucion completa",
            "toda la distribucion",
            "todos los tipos",
            "todos los tipos de consulta",
            "todas las consultas",
            "que tipo de consultas han habido",
            "que tipos de consulta han habido",
            "distribucion del trafico dns",
        ]

        top1_clues = [
            "que tipo dns predomina",
            "cual es el tipo de consulta mas frecuente",
            "cual es el tipo dns mas frecuente",
            "tipo de trafico dns mas frecuente",
        ]

        if any(
            clue in normalized
            for clue in full_distribution_clues
        ):
            top_n = None
            full_distribution = True

        elif any(
            clue in normalized
            for clue in top1_clues
        ):
            top_n = 1

        elif top_n == 1 and any(
            clue in normalized
            for clue in [
                "resume",
                "tipos dns",
                "tipos de consulta",
                "tipos de trafico dns",
                "top tipos",
            ]
        ):
            top_n = 3

        return {
            "ok": True,
            "intent": "dns_query_types_summary",
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": top_n,
            "full_distribution": full_distribution,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Count a specific DNS query type
    if intent == "dns_query_type_count":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        query_type = extract_query_type_from_query(original_text)

        return {
            "ok": True,
            "intent": "dns_query_type_count",
            "host": None,
            "hosts": [],
            "query_type": query_type,
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # List active DNS clients
    if intent == "dns_active_clients_list":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        top_n = detect_top_n(
            normalized,
            default=None
        )

        return {
            "ok": True,
            "intent": "dns_active_clients_list",
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": top_n,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Top DNS clients
    if intent == "dns_top_clients":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        top_n = detect_top_n(
            normalized,
            default=1
        )

        explicit_number_requested = (
            re.search(r"\b\d+\b", normalized) is not None
        )

        if (
            top_n == 1
            and not explicit_number_requested
            and any(
                clue in normalized
                for clue in [
                    "lista de clientes",
                    "lista de clientes activos",
                    "sacame una lista de los clientes activos",
                    "dime los clientes mas activos",
                    "clientes activos",
                    "clientes mas activos",
                    "clientes mas frecuentes",
                    "top clientes",
                    "sacame una lista de los clientes con mas consultas",
                    "clientes con mas consultas",
                    "lista de los clientes con mas consultas",
                    "clientes que mas consultas hacen",
                    "clientes con mas actividad",
                ]
            )
        ):
            top_n = 5

        return {
            "ok": True,
            "intent": "dns_top_clients",
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": top_n,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Top DNS domains
    if intent == "dns_top_domains":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        top_n = detect_top_n(
            normalized,
            default=1
        )

        if top_n == 1 and any(
            clue in normalized
            for clue in [
                "dominios",
                "los dominios",
                "mas consultados",
                "mas usados",
                "con mas consultas",
                "dime los dominios",
            ]
        ):
            top_n = 5

        return {
            "ok": True,
            "intent": "dns_top_domains",
            "host": None,
            "hosts": [],
            "time_range": time_range,
            "top_n": top_n,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Count queries for a specific domain
    if intent == "dns_domain_query_count":
        time_range = detect_dynamic_time_range(
            normalized,
            default="-6h"
        )

        domain = extract_domain_from_query(original_text)

        return {
            "ok": True,
            "intent": "dns_domain_query_count",
            "host": None,
            "hosts": [],
            "domain": domain,
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Overall status of all monitored hosts
    if intent == "hosts_status":
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

    # Current CPU status for one host
    if intent == "cpu_status":
        return {
            "ok": True,
            "intent": "cpu_status",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # CPU comparison between hosts
    if intent == "cpu_compare_hosts":
        time_range = detect_dynamic_time_range(
            normalized,
            default="now"
        )

        compare_hosts = (
            hosts
            if len(hosts) >= 2
            else SUPPORTED_HOSTS[:]
        )

        return {
            "ok": True,
            "intent": "cpu_compare_hosts",
            "host": None,
            "hosts": compare_hosts,
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Disk usage percentage
    if intent == "disk_used_pct":
        return {
            "ok": True,
            "intent": "disk_used_pct",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # General disk status
    if intent == "disk_status":
        return {
            "ok": True,
            "intent": "disk_status",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }


        # Disk comparison between hosts
    if intent == "disk_compare_hosts":
        selected_hosts = (
            hosts
            if len(hosts) >= 2
            else SUPPORTED_HOSTS[:]
        )

        compare_mode = detect_disk_compare_mode(normalized)

        return {
            "ok": True,
            "intent": "disk_compare_hosts",
            "host": None,
            "hosts": selected_hosts,
            "time_range": "now",
            "top_n": None,
            "compare_mode": compare_mode,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # General RAM status
    if intent == "ram_status":
        return {
            "ok": True,
            "intent": "ram_status",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # RAM comparison between hosts
    if intent == "ram_compare_hosts":
        selected_hosts = (
            hosts
            if len(hosts) >= 2
            else SUPPORTED_HOSTS[:]
        )

        compare_mode = detect_compare_mode(normalized)

        return {
            "ok": True,
            "intent": "ram_compare_hosts",
            "host": None,
            "hosts": selected_hosts,
            "time_range": "now",
            "top_n": None,
            "compare_mode": compare_mode,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # RAM usage percentage
    if intent == "ram_used_pct":
        return {
            "ok": True,
            "intent": "ram_used_pct",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Available RAM
    if intent == "ram_available":
        return {
            "ok": True,
            "intent": "ram_available",
            "host": host,
            "hosts": [],
            "time_range": "now",
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # General status of one host
    if host and intent == "host_status":
        time_range = detect_dynamic_time_range(
            normalized,
            default="now"
        )

        return {
            "ok": True,
            "intent": "host_status",
            "host": host,
            "hosts": [host],
            "time_range": time_range,
            "top_n": None,
            "raw_text": user_input,
            "normalized_text": normalized,
            "used_context": False,
        }

    # Handle follow-up queries using the previous context
    if last_context:
        last_intent = last_context.get("intent")

        # Follow-up after a RAM comparison
        if last_intent == "ram_compare_hosts":
            selected_hosts = (
                last_context.get("hosts")
                or SUPPORTED_HOSTS[:]
            )

            if (
                "menos" in normalized
                or "el que menos" in normalized
                or "cual es el que menos" in normalized
            ):
                return {
                    "ok": True,
                    "intent": "ram_compare_hosts",
                    "host": None,
                    "hosts": selected_hosts,
                    "time_range": "now",
                    "top_n": None,
                    "compare_mode": "min",
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

            if (
                "mas" in normalized
                or "el que mas" in normalized
                or "cual es el que mas" in normalized
            ):
                return {
                    "ok": True,
                    "intent": "ram_compare_hosts",
                    "host": None,
                    "hosts": selected_hosts,
                    "time_range": "now",
                    "top_n": None,
                    "compare_mode": "max",
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

        # Follow-up after a disk comparison
        if last_intent == "disk_compare_hosts":
            selected_hosts = (
                last_context.get("hosts")
                or SUPPORTED_HOSTS[:]
            )

            if (
                "menos" in normalized
                or "el que menos" in normalized
                or "quien menos" in normalized
                or "cual es el que menos" in normalized
            ):
                return {
                    "ok": True,
                    "intent": "disk_compare_hosts",
                    "host": None,
                    "hosts": selected_hosts,
                    "time_range": "now",
                    "top_n": None,
                    "compare_mode": "min",
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

            if (
                "mas" in normalized
                or "el que mas" in normalized
                or "quien mas" in normalized
                or "cual es el que mas" in normalized
            ):
                return {
                    "ok": True,
                    "intent": "disk_compare_hosts",
                    "host": None,
                    "hosts": selected_hosts,
                    "time_range": "now",
                    "top_n": None,
                    "compare_mode": "max",
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

        # Follow-up questions that mention another host
        if host:
            if (
                last_intent == "cpu_status"
                and is_cpu_follow_up_query(normalized, host)
            ):
                return {
                    "ok": True,
                    "intent": "cpu_status",
                    "host": host,
                    "hosts": [],
                    "time_range": "now",
                    "top_n": None,
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

            if is_follow_up_query(normalized, host):
                if last_intent == "host_status":
                    time_range = detect_dynamic_time_range(
                        normalized,
                        default="now"
                    )

                    return {
                        "ok": True,
                        "intent": "host_status",
                        "host": host,
                        "hosts": [host],
                        "time_range": time_range,
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "cpu_status":
                    return {
                        "ok": True,
                        "intent": "cpu_status",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "ram_status":
                    return {
                        "ok": True,
                        "intent": "ram_status",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "ram_used_pct":
                    return {
                        "ok": True,
                        "intent": "ram_used_pct",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "ram_available":
                    return {
                        "ok": True,
                        "intent": "ram_available",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "disk_status":
                    return {
                        "ok": True,
                        "intent": "disk_status",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

                if last_intent == "disk_used_pct":
                    return {
                        "ok": True,
                        "intent": "disk_used_pct",
                        "host": host,
                        "hosts": [],
                        "time_range": "now",
                        "top_n": None,
                        "raw_text": user_input,
                        "normalized_text": normalized,
                        "used_context": True,
                    }

        # Follow-up asking for another DNS query type
        if (
            last_intent == "dns_query_type_count"
            and is_dns_query_type_follow_up(normalized)
        ):
            query_type = extract_query_type_from_query(original_text)
            time_range = last_context.get("time_range", "-6h")

            return {
                "ok": True,
                "intent": "dns_query_type_count",
                "host": None,
                "hosts": [],
                "query_type": query_type,
                "time_range": time_range,
                "top_n": None,
                "raw_text": user_input,
                "normalized_text": normalized,
                "used_context": True,
            }

        # Follow-up between forwarded and cached queries
        if (
            last_intent in [
                "dns_forwarded_count",
                "dns_cached_count",
                "dns_forwarded_vs_cached_summary",
            ]
            and is_forwarded_cached_follow_up(normalized)
        ):
            mode = extract_forwarded_cached_mode(normalized)
            time_range = last_context.get("time_range", "-6h")

            if mode == "forwarded":
                return {
                    "ok": True,
                    "intent": "dns_forwarded_count",
                    "host": None,
                    "hosts": [],
                    "time_range": time_range,
                    "top_n": None,
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

            if mode == "cached":
                return {
                    "ok": True,
                    "intent": "dns_cached_count",
                    "host": None,
                    "hosts": [],
                    "time_range": time_range,
                    "top_n": None,
                    "raw_text": user_input,
                    "normalized_text": normalized,
                    "used_context": True,
                }

    # Return an error when the query does not match any supported intent
    return {
        "ok": False,
        "intent": None,
        "host": host,
        "hosts": hosts,
        "domain": extract_domain_from_query(original_text),
        "time_range": None,
        "query_type": extract_query_type_from_query(original_text),
        "top_n": None,
        "raw_text": user_input,
        "normalized_text": normalized,
        "error": "No se ha podido interpretar la consulta dentro del dominio soportado."
    }


