import re


# Display names used when building responses for each host
HOST_PRESENTATION = {
    "raspberry": {
        "display_name": "la Raspberry",
        "compare_name": "la Raspberry",
        "gender": "f",
    },
    "ASUS_Josemi": {
        "display_name": "el host ASUS_Josemi",
        "compare_name": "ASUS_Josemi",
        "gender": "m",
    },
}


def get_host_metadata(host: str) -> dict:
    # Return the display information associated with a host
    return HOST_PRESENTATION.get(
        host,
        {
            "display_name": host,
            "compare_name": host,
            "gender": "m",
        }
    )


def get_display_host_name(host: str) -> str:
    # Return the host name used in normal responses
    return get_host_metadata(host)["display_name"]


def get_compare_host_name(host: str) -> str:
    # Return the shorter host name used in comparisons
    return get_host_metadata(host)["compare_name"]


def classify_load(load1: float) -> str:
    # Classify the current system load into simple levels
    if load1 is None:
        return "desconocida"

    if load1 < 0.7:
        return "baja"

    if load1 < 1.5:
        return "moderada"

    return "alta"


def classify_overall_status(
    load1: float,
    ram_used: float,
    disk_used: float
) -> str:
    # Determine the overall host status from the main system metrics
    if load1 is None or ram_used is None or disk_used is None:
        return "indeterminado"

    if load1 >= 2.0 or ram_used >= 85 or disk_used >= 90:
        return "a revisar"

    if load1 >= 1.0 or ram_used >= 70 or disk_used >= 80:
        return "estable"

    return "correcto"


def build_status_intro(
    display_host: str,
    gender: str,
    overall_status: str
) -> str:
    # Build the first sentence of a host status response
    operativo = "operativa" if gender == "f" else "operativo"

    if overall_status == "correcto":
        return (
            f"{display_host.capitalize()} se encuentra {operativo} "
            "y presenta un estado general correcto."
        )

    if overall_status == "estable":
        return (
            f"{display_host.capitalize()} se encuentra {operativo} "
            "y presenta un estado general estable."
        )

    if overall_status == "a revisar":
        return (
            f"{display_host.capitalize()} se encuentra {operativo}, "
            "aunque presenta algunos indicadores que conviene revisar."
        )

    return (
        f"No se ha podido determinar con claridad el estado general "
        f"de {display_host}."
    )


def format_host_status_response(host: str, metrics: dict) -> str:
    # Build a general status response for one host
    metadata = get_host_metadata(host)
    display_host = metadata["display_name"]
    gender = metadata["gender"]

    load1 = metrics.get("load1")
    ram_used = metrics.get("ram_used_percent")
    disk_used = metrics.get("disk_used_percent")

    if load1 is None or ram_used is None or disk_used is None:
        return (
            f"No se ha podido obtener el estado completo de {display_host}. "
            "Es posible que falten métricas recientes en InfluxDB."
        )

    load_label = classify_load(load1)
    overall_status = classify_overall_status(
        load1,
        ram_used,
        disk_used
    )

    intro = build_status_intro(
        display_host,
        gender,
        overall_status
    )

    return (
        f"{intro} "
        f"La carga actual es {load_label} (load1 = {load1:.2f}), "
        f"la RAM usada es del {ram_used:.1f} % "
        f"y el disco principal presenta una ocupación del {disk_used:.1f} %."
    )


def format_cpu_compare_response(loads_by_host: dict) -> str:
    # Compare the current system load between two hosts
    valid_items = [
        (host, value)
        for host, value in loads_by_host.items()
        if value is not None
    ]

    if len(valid_items) < 2:
        return (
            "No se ha podido realizar la comparación de carga entre hosts. "
            "Es posible que falten métricas recientes en InfluxDB."
        )

    sorted_hosts = sorted(
        valid_items,
        key=lambda item: item[1],
        reverse=True
    )

    host_a, load_a = sorted_hosts[0]
    host_b, load_b = sorted_hosts[1]

    display_a = get_compare_host_name(host_a)
    display_b = get_compare_host_name(host_b)

    if abs(load_a - load_b) < 0.05:
        return (
            f"Actualmente {display_a} y {display_b} presentan una carga muy similar. "
            f"Los valores de load1 son {load_a:.2f} y {load_b:.2f}, respectivamente."
        )

    return (
        f"Actualmente {display_a} presenta mayor carga que {display_b}. "
        f"El valor de load1 es {load_a:.2f} frente a {load_b:.2f}."
    )


def _format_period_text(time_range: str) -> str:
    # Convert a Flux time range into natural language
    if time_range == "today":
        return "hoy"

    if time_range == "now":
        return "en los últimos minutos"

    if not isinstance(time_range, str) or not time_range.startswith("-"):
        return "en el periodo solicitado"

    raw = time_range[1:]

    match = re.match(r"(\d+)(m|h|d|w|mo|y)$", raw)

    if not match:
        return "en el periodo solicitado"

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "m":
        return (
            "en el último minuto"
            if amount == 1
            else f"en los últimos {amount} minutos"
        )

    if unit == "h":
        return (
            "en la última hora"
            if amount == 1
            else f"en las últimas {amount} horas"
        )

    if unit == "d":
        return (
            "en el último día"
            if amount == 1
            else f"en los últimos {amount} días"
        )

    if unit == "w":
        return (
            "en la última semana"
            if amount == 1
            else f"en las últimas {amount} semanas"
        )

    if unit == "mo":
        return (
            "en el último mes"
            if amount == 1
            else f"en los últimos {amount} meses"
        )

    if unit == "y":
        return (
            "en el último año"
            if amount == 1
            else f"en los últimos {amount} años"
        )

    return "en el periodo solicitado"


def format_dns_top_domains_response(
    top_domains: list,
    time_range: str
) -> str:
    # Format the most queried DNS domains
    if not top_domains:
        return (
            "No se han podido obtener datos de dominios DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    if len(top_domains) == 1:
        top_domain = top_domains[0]
        domain = top_domain["domain"]
        count = top_domain["count"]

        return (
            f"{period_text.capitalize()}, el dominio más consultado ha sido "
            f"{domain}, con {int(count)} consultas acumuladas."
        )

    formatted_items = []

    for i, item in enumerate(top_domains, start=1):
        domain = item["domain"]
        count = int(item["count"])

        formatted_items.append(
            f"{i}. {domain} ({count})"
        )

    joined_items = " | ".join(formatted_items)

    return (
        f"{period_text.capitalize()}, los dominios más consultados han sido: "
        f"{joined_items}."
    )


def format_dns_top_clients_response(
    top_clients: list,
    time_range: str
) -> str:
    # Format the clients with the highest DNS activity
    if not top_clients:
        return (
            "No se han podido obtener datos de clientes DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    if len(top_clients) == 1:
        top_client = top_clients[0]
        client = top_client["client"]
        count = top_client["count"]

        return (
            f"{period_text.capitalize()}, el cliente más activo ha sido "
            f"{client}, con {int(count)} consultas DNS acumuladas."
        )

    formatted_items = []

    for i, item in enumerate(top_clients, start=1):
        client = item["client"]
        count = int(item["count"])

        formatted_items.append(
            f"{i}. {client} ({count})"
        )

    joined_items = " | ".join(formatted_items)

    return (
        f"{period_text.capitalize()}, los clientes más activos han sido: "
        f"{joined_items}."
    )


def format_dns_active_clients_list_response(
    active_clients: list,
    time_range: str,
    requested_n: int = None
) -> str:
    # Format the list of clients with DNS activity
    if not active_clients:
        return (
            "No se han podido obtener clientes con actividad DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    if len(active_clients) == 1:
        return (
            f"{period_text.capitalize()}, se ha detectado un único cliente "
            f"con actividad DNS: {active_clients[0]}."
        )

    if len(active_clients) == 2:
        clients_text = (
            f"{active_clients[0]} y {active_clients[1]}"
        )
    else:
        clients_text = (
            ", ".join(active_clients[:-1])
            + f" y {active_clients[-1]}"
        )

    if requested_n:
        return (
            f"{period_text.capitalize()}, estos son los "
            f"{len(active_clients)} clientes con actividad DNS solicitados: "
            f"{clients_text}."
        )

    return (
        f"{period_text.capitalize()}, los clientes con actividad DNS "
        f"registrada han sido: {clients_text}."
    )


def format_dns_summary_response(
    metrics: dict,
    time_range: str
) -> str:
    # Build a general summary of DNS activity
    total_queries = metrics.get("total_queries")
    qps = metrics.get("qps")
    blocked_pct = metrics.get("blocked_pct")
    cached_pct = metrics.get("cached_pct")

    if any(
        value is None
        for value in [
            total_queries,
            qps,
            blocked_pct,
            cached_pct,
        ]
    ):
        return (
            "No se ha podido construir el resumen DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, se han registrado "
        f"{int(total_queries)} consultas DNS. "
        f"El QPS medio observado ha sido {qps:.2f} req/s, "
        f"el {blocked_pct:.2f} % de las consultas fueron bloqueadas "
        f"y el {cached_pct:.2f} % se resolvieron desde caché."
    )


def format_dns_total_queries_response(
    total_queries,
    time_range: str
) -> str:
    # Format the total number of DNS queries
    if total_queries is None:
        return (
            "No se ha podido obtener el total de consultas DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, se han registrado "
        f"{int(total_queries)} consultas DNS."
    )


def format_dns_domain_query_count_response(
    domain: str,
    total: int,
    time_range: str
) -> str:
    # Format the number of queries made to a specific domain
    period_text = _format_period_text(time_range)

    if total <= 0:
        return (
            f"{period_text.capitalize()}, no se han registrado consultas DNS "
            f"para el dominio {domain}."
        )

    return (
        f"{period_text.capitalize()}, el dominio {domain} "
        f"ha acumulado {total} consultas DNS."
    )


def format_dns_qps_response(qps, time_range: str) -> str:
    # Format the average DNS queries per second
    if qps is None:
        return (
            "No se ha podido obtener el QPS medio "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, el QPS observado "
        f"ha sido {qps:.2f} req/s."
    )


def format_dns_blocked_pct_response(
    blocked_pct,
    time_range: str
) -> str:
    # Format the percentage of blocked DNS queries
    if blocked_pct is None:
        return (
            "No se ha podido obtener el porcentaje de consultas bloqueadas "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, el {blocked_pct:.2f} % "
        "de las consultas DNS fueron bloqueadas."
    )


def format_dns_cached_pct_response(
    cached_pct,
    time_range: str
) -> str:
    # Format the percentage of cached DNS queries
    if cached_pct is None:
        return (
            "No se ha podido obtener el porcentaje de consultas "
            "resueltas desde caché para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, el {cached_pct:.2f} % "
        "de las consultas DNS se resolvieron desde caché."
    )


def format_dns_active_clients_count_response(
    active_clients,
    time_range: str
) -> str:
    # Format the number of active DNS clients
    if active_clients is None:
        return (
            "No se ha podido obtener el número de clientes activos "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, se detectaron "
        f"{int(active_clients)} clientes activos."
    )


def format_dns_query_types_summary_response(
    query_types: list,
    time_range: str,
    full_distribution: bool = False
) -> str:
    # Format the distribution of DNS query types
    if not query_types:
        return (
            "No se han podido obtener datos de tipos de consulta DNS "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    total = sum(
        int(item["count"])
        for item in query_types
        if item.get("count") is not None
    )

    if total == 0:
        return (
            "No se han podido obtener datos de tipos de consulta DNS "
            "para el periodo solicitado."
        )

    enriched = []

    for item in query_types:
        type_name = item["type"]
        count = int(item["count"])
        pct = (count / total) * 100

        enriched.append({
            "type": type_name,
            "count": count,
            "pct": pct,
        })

    if full_distribution:
        formatted = " | ".join(
            f"{item['type']} ({item['count']}, {item['pct']:.1f} %)"
            for item in enriched
        )

        return (
            f"{period_text.capitalize()}, la distribución completa "
            f"de tipos DNS ha sido: {formatted}."
        )

    if len(enriched) == 1:
        first = enriched[0]

        return (
            f"{period_text.capitalize()}, el tipo DNS más frecuente ha sido "
            f"{first['type']}, con un {first['pct']:.1f} % del total."
        )

    if len(enriched) <= 3:
        first = enriched[0]
        second = enriched[1] if len(enriched) > 1 else None
        third = enriched[2] if len(enriched) > 2 else None

        if second and third:
            return (
                f"{period_text.capitalize()}, el tipo DNS predominante ha sido "
                f"{first['type']}, con un {first['pct']:.1f} % del total. "
                f"Le siguen {second['type']} con un {second['pct']:.1f} % "
                f"y {third['type']} con un {third['pct']:.1f} %."
            )

        if second:
            return (
                f"{period_text.capitalize()}, el tipo DNS predominante ha sido "
                f"{first['type']}, con un {first['pct']:.1f} % del total. "
                f"Le sigue {second['type']} con un {second['pct']:.1f} %."
            )

    first = enriched[0]

    return (
        f"{period_text.capitalize()}, el tipo DNS más frecuente ha sido "
        f"{first['type']}, con un {first['pct']:.1f} % del total."
    )


def format_dns_forwarded_vs_cached_summary_response(
    metrics: dict,
    time_range: str
) -> str:
    # Compare forwarded and cached DNS queries
    forwarded = metrics.get("forwarded")
    cached = metrics.get("cached")

    if forwarded is None or cached is None:
        return (
            "No se ha podido obtener la comparativa entre consultas "
            "forwarded y cached para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)
    total = forwarded + cached

    if total == 0:
        return (
            "No se han detectado consultas forwarded ni cached "
            "en el periodo solicitado."
        )

    forwarded_pct = (forwarded / total) * 100
    cached_pct = (cached / total) * 100

    if abs(forwarded - cached) < max(1, total * 0.03):
        return (
            f"{period_text.capitalize()}, el reparto entre consultas forwarded "
            f"y cached ha sido muy equilibrado. "
            f"Se han contabilizado {int(forwarded)} reenviadas "
            f"({forwarded_pct:.1f} %) frente a {int(cached)} resueltas "
            f"desde caché ({cached_pct:.1f} %)."
        )

    if forwarded > cached:
        return (
            f"{period_text.capitalize()}, han predominado las consultas reenviadas. "
            f"Se han contabilizado {int(forwarded)} consultas forwarded "
            f"({forwarded_pct:.1f} %) frente a {int(cached)} resueltas "
            f"desde caché ({cached_pct:.1f} %)."
        )

    return (
        f"{period_text.capitalize()}, han predominado las consultas "
        f"resueltas desde caché. "
        f"Se han contabilizado {int(cached)} consultas cached "
        f"({cached_pct:.1f} %) frente a {int(forwarded)} reenviadas "
        f"({forwarded_pct:.1f} %)."
    )


def format_dns_forwarded_count_response(
    forwarded,
    time_range: str
) -> str:
    # Format the number of forwarded DNS queries
    if forwarded is None:
        return (
            "No se ha podido obtener el número de consultas reenviadas "
            "para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, se contabilizaron "
        f"{int(forwarded)} consultas reenviadas."
    )


def format_dns_cached_count_response(
    cached,
    time_range: str
) -> str:
    # Format the number of cached DNS queries
    if cached is None:
        return (
            "No se ha podido obtener el número de consultas resueltas "
            "desde caché para el periodo solicitado."
        )

    period_text = _format_period_text(time_range)

    return (
        f"{period_text.capitalize()}, se contabilizaron "
        f"{int(cached)} consultas resueltas desde caché."
    )


def format_ram_status_response(
    host: str,
    ram_metrics: dict
) -> str:
    # Build a general RAM status response
    used_percent = ram_metrics.get("used_percent")
    used_gb = ram_metrics.get("used")
    available_gb = ram_metrics.get("available")
    total_gb = ram_metrics.get("total")

    if any(
        value is None
        for value in [
            used_percent,
            used_gb,
            available_gb,
            total_gb,
        ]
    ):
        return (
            f"No se han podido obtener correctamente las métricas de RAM "
            f"para {get_display_host_name(host)}."
        )

    host_text = get_display_host_name(host)

    return (
        f"Actualmente, {host_text} utiliza un {used_percent:.1f} % de la RAM. "
        f"Esto equivale a {used_gb:.2f} GB usados de un total de "
        f"{total_gb:.2f} GB, con aproximadamente {available_gb:.2f} GB disponibles."
    )


def format_ram_compare_response(
    host_metrics: dict,
    compare_mode: str = "max",
    comparison_style: str = None
) -> str:
    # Compare RAM usage between the selected hosts
    valid = {
        host: metrics
        for host, metrics in host_metrics.items()
        if metrics and metrics.get("used_percent") is not None
    }

    if len(valid) < 2:
        return (
            "No se ha podido realizar correctamente la comparación "
            "de RAM entre los hosts seleccionados."
        )

    sorted_hosts = sorted(
        valid.items(),
        key=lambda item: item[1]["used_percent"]
    )

    if compare_mode == "min":
        first_host, first_metrics = sorted_hosts[0]
        second_host, second_metrics = sorted_hosts[1]
    else:
        first_host, first_metrics = sorted_hosts[-1]
        second_host, second_metrics = sorted_hosts[0]

    first_pct = first_metrics["used_percent"]
    second_pct = second_metrics["used_percent"]

    first_name = get_compare_host_name(first_host)
    second_name = get_compare_host_name(second_host)

    if comparison_style == "worst_best":
        if compare_mode == "min":
            return (
                f"El host que va mejor de memoria RAM ahora mismo es {first_name}. "
                f"Tiene una ocupación del {first_pct:.1f} % frente al "
                f"{second_pct:.1f} % de {second_name}. "
                f"En valores absolutos, {first_name} usa "
                f"{first_metrics['used']:.2f} GB y {second_name} usa "
                f"{second_metrics['used']:.2f} GB."
            )

        return (
            f"El host que va peor de memoria RAM ahora mismo es {first_name}. "
            f"Tiene una ocupación del {first_pct:.1f} % frente al "
            f"{second_pct:.1f} % de {second_name}. "
            f"En valores absolutos, {first_name} usa "
            f"{first_metrics['used']:.2f} GB y {second_name} usa "
            f"{second_metrics['used']:.2f} GB."
        )

    if compare_mode == "min":
        return (
            f"Actualmente {first_name} presenta una menor ocupación de memoria "
            f"que {second_name}. La RAM usada es del {first_pct:.1f} % "
            f"frente al {second_pct:.1f} %. "
            f"En valores absolutos, {first_name} usa "
            f"{first_metrics['used']:.2f} GB y {second_name} usa "
            f"{second_metrics['used']:.2f} GB."
        )

    return (
        f"Actualmente {first_name} presenta una mayor ocupación de memoria "
        f"que {second_name}. La RAM usada es del {first_pct:.1f} % "
        f"frente al {second_pct:.1f} %. "
        f"En valores absolutos, {first_name} usa "
        f"{first_metrics['used']:.2f} GB y {second_name} usa "
        f"{second_metrics['used']:.2f} GB."
    )


def format_ram_used_pct_response(
    host: str,
    ram_metrics: dict
) -> str:
    # Format the current RAM usage percentage
    used_percent = ram_metrics.get("used_percent")
    used_gb = ram_metrics.get("used")
    total_gb = ram_metrics.get("total")

    if any(
        value is None
        for value in [
            used_percent,
            used_gb,
            total_gb,
        ]
    ):
        return (
            f"No se han podido obtener correctamente las métricas de RAM "
            f"para {get_display_host_name(host)}."
        )

    host_text = get_display_host_name(host)

    return (
        f"Actualmente, {host_text} utiliza un {used_percent:.1f} % de la RAM, "
        f"lo que equivale a {used_gb:.2f} GB usados de un total "
        f"de {total_gb:.2f} GB."
    )


def format_ram_available_response(
    host: str,
    ram_metrics: dict
) -> str:
    # Format the amount of available RAM
    available_gb = ram_metrics.get("available")
    total_gb = ram_metrics.get("total")
    used_percent = ram_metrics.get("used_percent")

    if any(
        value is None
        for value in [
            available_gb,
            total_gb,
            used_percent,
        ]
    ):
        return (
            f"No se han podido obtener correctamente las métricas de RAM "
            f"para {get_display_host_name(host)}."
        )

    host_text = get_display_host_name(host)

    return (
        f"Actualmente, {host_text} tiene aproximadamente "
        f"{available_gb:.2f} GB de RAM disponibles de un total de "
        f"{total_gb:.2f} GB. La ocupación actual es del "
        f"{used_percent:.1f} %."
    )


def format_disk_used_pct_response(
    host: str,
    disk_metrics: dict
) -> str:
    # Format the current disk usage percentage
    used_percent = disk_metrics.get("used_percent")

    if used_percent is None:
        return (
            f"No se han podido obtener correctamente las métricas de disco "
            f"para {get_display_host_name(host)}."
        )

    host_text = get_display_host_name(host)

    return (
        f"Actualmente, {host_text} tiene ocupado un "
        f"{used_percent:.1f} % del disco principal."
    )


def format_disk_status_response(
    host: str,
    disk_metrics: dict
) -> str:
    # Build a general disk status response
    used_percent = disk_metrics.get("used_percent")

    if used_percent is None:
        return (
            f"No se han podido obtener correctamente las métricas de disco "
            f"para {get_display_host_name(host)}."
        )

    host_text = get_display_host_name(host).capitalize()

    if used_percent < 60:
        state = "presenta un estado de almacenamiento correcto"
    elif used_percent < 80:
        state = "presenta un nivel de ocupación moderado"
    else:
        state = "presenta una ocupación elevada de almacenamiento"

    return (
        f"{host_text} {state}. "
        f"El disco principal está ocupado al {used_percent:.1f} %."
    )


def format_disk_compare_response(
    host_metrics: dict,
    compare_mode: str = "max"
) -> str:
    # Compare disk usage between the selected hosts
    valid = {
        host: metrics
        for host, metrics in host_metrics.items()
        if metrics and metrics.get("used_percent") is not None
    }

    if len(valid) < 2:
        return (
            "No se ha podido realizar correctamente la comparación "
            "de disco entre los hosts seleccionados."
        )

    sorted_hosts = sorted(
        valid.items(),
        key=lambda item: item[1]["used_percent"]
    )

    if compare_mode == "min":
        first_host, first_metrics = sorted_hosts[0]
        second_host, second_metrics = sorted_hosts[1]
    else:
        first_host, first_metrics = sorted_hosts[-1]
        second_host, second_metrics = sorted_hosts[0]

    first_pct = first_metrics["used_percent"]
    second_pct = second_metrics["used_percent"]

    first_name = get_compare_host_name(first_host)
    second_name = get_compare_host_name(second_host)

    if compare_mode == "min":
        return (
            f"Actualmente {first_name} presenta una menor ocupación de disco "
            f"que {second_name}. El porcentaje de uso del disco principal "
            f"es del {first_pct:.1f} % frente al {second_pct:.1f} %."
        )

    return (
        f"Actualmente {first_name} presenta una mayor ocupación de disco "
        f"que {second_name}. El porcentaje de uso del disco principal "
        f"es del {first_pct:.1f} % frente al {second_pct:.1f} %."
    )


def format_dns_query_type_count_response(
    query_type: str,
    total: int,
    time_range: str
) -> str:
    # Format the number of queries for a specific DNS type
    period_text = _format_period_text(time_range)

    if total <= 0:
        return (
            f"{period_text.capitalize()}, no se han registrado consultas DNS "
            f"de tipo {query_type}."
        )

    return (
        f"{period_text.capitalize()}, se han registrado "
        f"{total} consultas DNS de tipo {query_type}."
    )


def format_cpu_status_response(
    host: str,
    metrics: dict
) -> str:
    # Format the current CPU load for one host
    if not metrics:
        return (
            f"No se ha podido obtener la carga actual de "
            f"{get_display_host_name(host)}."
        )

    load1 = metrics.get("load1")

    if load1 is None:
        return (
            f"No se ha podido obtener la carga actual de "
            f"{get_display_host_name(host)}."
        )

    host_label = get_display_host_name(host)
    level = classify_load(load1)

    return (
        f"Actualmente {host_label} presenta una carga {level} "
        f"(load1 = {load1:.2f})."
    )


def format_hosts_status_response(metrics_by_host: dict) -> str:
    # Build a combined status response for both monitored hosts
    raspberry_metrics = metrics_by_host.get("raspberry")
    pc_metrics = metrics_by_host.get("ASUS_Josemi")

    if not raspberry_metrics or not pc_metrics:
        return (
            "No se ha podido obtener el estado completo de ambos hosts."
        )

    def describe_host(host_name: str, metrics: dict) -> str:
        load1 = metrics.get("load1")
        ram_used_pct = metrics.get("ram_used_pct")
        disk_used_pct = metrics.get("disk_used_pct")

        if (
            load1 is None
            or ram_used_pct is None
            or disk_used_pct is None
        ):
            return (
                f"No se ha podido obtener el estado completo de "
                f"{get_display_host_name(host_name)}."
            )

        load_desc = classify_load(load1)
        label = get_display_host_name(host_name).capitalize()

        return (
            f"{label} está operativa"
            if host_name == "raspberry"
            else f"{label} está operativo"
        ) + (
            f", con carga {load_desc} "
            f"(load1 = {load1:.2f}), RAM al {ram_used_pct:.1f} % "
            f"y disco al {disk_used_pct:.1f} %."
        )

    raspberry_text = describe_host(
        "raspberry",
        raspberry_metrics
    )

    pc_text = describe_host(
        "ASUS_Josemi",
        pc_metrics
    )

    return f"{raspberry_text} {pc_text}"

