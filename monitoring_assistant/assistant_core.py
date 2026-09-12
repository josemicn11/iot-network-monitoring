from intent_parser import parse_user_query
from llm_router import parse_user_query_with_llm
from response_formatter import (
    format_host_status_response,
    format_cpu_compare_response,
    format_dns_top_domains_response,
    format_dns_top_clients_response,
    format_dns_active_clients_list_response,
    format_dns_summary_response,
    format_dns_total_queries_response,
    format_dns_qps_response,
    format_dns_blocked_pct_response,
    format_dns_cached_pct_response,
    format_dns_active_clients_count_response,
    format_dns_query_types_summary_response,
    format_dns_forwarded_vs_cached_summary_response,
    format_dns_forwarded_count_response,
    format_dns_cached_count_response,
    format_ram_status_response,
    format_ram_compare_response,
    format_ram_used_pct_response,
    format_ram_available_response,
    format_disk_used_pct_response,
    format_disk_status_response,
    format_disk_compare_response,
    format_cpu_status_response,
    format_hosts_status_response,
    format_dns_domain_query_count_response,
    format_dns_query_type_count_response,
)


def process_user_message(user_input, last_context, influx_client):
    # Try the rule-based parser first
    parsed_query = parse_user_query(
        user_input,
        last_context=last_context
    )

    # Use the LLM router only if the local parser cannot understand the query
    if not parsed_query["ok"]:
        llm_parsed_query = parse_user_query_with_llm(
            user_input,
            last_context=last_context
        )

        if llm_parsed_query["ok"]:
            parsed_query = llm_parsed_query
        else:
            return (
                "No he entendido bien la consulta. "
                "Prueba a reformularla o pregúntame "
                "\"qué te puedo preguntar\" para ver ejemplos "
                "de cosas que sí puedo consultar.",
                last_context
            )

    # Store the relevant information for possible follow-up queries
    updated_context = dict(last_context)

    updated_context["intent"] = parsed_query["intent"]
    updated_context["host"] = parsed_query.get("host")
    updated_context["hosts"] = parsed_query.get("hosts", [])
    updated_context["compare_mode"] = parsed_query.get("compare_mode")
    updated_context["comparison_style"] = parsed_query.get("comparison_style")
    updated_context["time_range"] = parsed_query.get("time_range")
    updated_context["query_type"] = parsed_query.get("query_type")
    updated_context["full_distribution"] = parsed_query.get("full_distribution")
    updated_context["domain"] = parsed_query.get("domain")

    intent = parsed_query["intent"]

    # RAM queries
    if intent == "ram_used_pct":
        host = parsed_query["host"]
        ram_metrics = influx_client.get_current_ram_metrics(host)

        response = format_ram_used_pct_response(
            host,
            ram_metrics
        )

        return response, updated_context

    if intent == "ram_available":
        host = parsed_query["host"]
        ram_metrics = influx_client.get_current_ram_metrics(host)

        response = format_ram_available_response(
            host,
            ram_metrics
        )

        return response, updated_context

    if intent == "ram_status":
        host = parsed_query["host"]
        ram_metrics = influx_client.get_current_ram_metrics(host)

        response = format_ram_status_response(
            host,
            ram_metrics
        )

        return response, updated_context

    if intent == "ram_compare_hosts":
        hosts = parsed_query["hosts"]
        compare_mode = parsed_query.get("compare_mode", "max")
        comparison_style = parsed_query.get("comparison_style")

        ram_metrics = influx_client.get_multiple_ram_metrics(hosts)

        response = format_ram_compare_response(
            ram_metrics,
            compare_mode=compare_mode,
            comparison_style=comparison_style
        )

        return response, updated_context

    # General host status
    if intent == "host_status":
        host = parsed_query["host"]

        if not host:
            return (
                "He identificado que quieres consultar el estado de un host, "
                "pero no he podido determinar cuál.",
                updated_context
            )

        metrics = influx_client.get_host_status_metrics(host)

        response = format_host_status_response(
            host,
            metrics
        )

        return response, updated_context

    if intent == "hosts_status":
        hosts = parsed_query.get(
            "hosts",
            ["raspberry", "ASUS_Josemi"]
        )

        metrics_by_host = {}

        for host in hosts:
            metrics_by_host[host] = (
                influx_client.get_host_status_metrics(host)
            )

        response = format_hosts_status_response(
            metrics_by_host
        )

        return response, updated_context

    # CPU queries
    if intent == "cpu_status":
        host = parsed_query["host"]
        metrics = influx_client.get_host_status_metrics(host)

        response = format_cpu_status_response(
            host,
            metrics
        )

        return response, updated_context

    if intent == "cpu_compare_hosts":
        hosts = parsed_query["hosts"]

        loads_by_host = (
            influx_client.get_multiple_current_load1(hosts)
        )

        response = format_cpu_compare_response(
            loads_by_host
        )

        return response, updated_context

    # DNS domain queries
    if intent == "dns_top_domains":
        time_range = parsed_query["time_range"]
        top_n = parsed_query["top_n"]

        top_domains = influx_client.get_top_domains(
            time_range=time_range,
            limit_n=top_n
        )

        response = format_dns_top_domains_response(
            top_domains,
            time_range
        )

        return response, updated_context

    if intent == "dns_domain_query_count":
        domain = parsed_query["domain"]
        time_range = parsed_query["time_range"]

        total = influx_client.get_dns_domain_query_count(
            domain,
            time_range
        )

        response = format_dns_domain_query_count_response(
            domain,
            total,
            time_range
        )

        return response, updated_context

    # DNS query type queries
    if intent == "dns_query_type_count":
        query_type = parsed_query["query_type"]
        time_range = parsed_query["time_range"]

        total = influx_client.get_dns_query_type_count(
            query_type,
            time_range
        )

        response = format_dns_query_type_count_response(
            query_type,
            total,
            time_range
        )

        return response, updated_context

    if intent == "dns_query_types_summary":
        time_range = parsed_query["time_range"]
        top_n = parsed_query["top_n"]
        full_distribution = parsed_query.get(
            "full_distribution",
            False
        )

        query_types = influx_client.get_dns_query_types_summary(
            time_range=time_range,
            limit_n=top_n
        )

        response = format_dns_query_types_summary_response(
            query_types,
            time_range,
            full_distribution=full_distribution
        )

        return response, updated_context

    # DNS client queries
    if intent == "dns_top_clients":
        time_range = parsed_query["time_range"]
        top_n = parsed_query["top_n"]

        top_clients = influx_client.get_top_clients(
            time_range=time_range,
            limit_n=top_n
        )

        response = format_dns_top_clients_response(
            top_clients,
            time_range
        )

        return response, updated_context

    if intent == "dns_active_clients_list":
        time_range = parsed_query["time_range"]
        top_n = parsed_query.get("top_n")

        active_clients = influx_client.get_active_clients_list(
            time_range=time_range
        )

        if top_n:
            active_clients = active_clients[:top_n]

        response = format_dns_active_clients_list_response(
            active_clients,
            time_range,
            requested_n=top_n
        )

        return response, updated_context

    if intent == "dns_active_clients_count":
        time_range = parsed_query["time_range"]

        active_clients = (
            influx_client.get_dns_active_clients_count(
                time_range=time_range
            )
        )

        response = format_dns_active_clients_count_response(
            active_clients,
            time_range
        )

        return response, updated_context

    # General DNS metrics
    if intent == "dns_summary":
        time_range = parsed_query["time_range"]

        metrics = influx_client.get_dns_summary_metrics(
            time_range=time_range
        )

        response = format_dns_summary_response(
            metrics,
            time_range
        )

        return response, updated_context

    if intent == "dns_total_queries":
        time_range = parsed_query["time_range"]

        total_queries = influx_client.get_dns_total_queries(
            time_range=time_range
        )

        response = format_dns_total_queries_response(
            total_queries,
            time_range
        )

        return response, updated_context

    if intent == "dns_qps":
        time_range = parsed_query["time_range"]

        qps = influx_client.get_dns_qps(
            time_range=time_range
        )

        response = format_dns_qps_response(
            qps,
            time_range
        )

        return response, updated_context

    if intent == "dns_blocked_pct":
        time_range = parsed_query["time_range"]

        blocked_pct = influx_client.get_dns_blocked_pct(
            time_range=time_range
        )

        response = format_dns_blocked_pct_response(
            blocked_pct,
            time_range
        )

        return response, updated_context

    if intent == "dns_cached_pct":
        time_range = parsed_query["time_range"]

        cached_pct = influx_client.get_dns_cached_pct(
            time_range=time_range
        )

        response = format_dns_cached_pct_response(
            cached_pct,
            time_range
        )

        return response, updated_context

    # Forwarded and cached DNS queries
    if intent == "dns_forwarded_vs_cached_summary":
        time_range = parsed_query["time_range"]

        metrics = (
            influx_client.get_dns_forwarded_vs_cached_metrics(
                time_range=time_range
            )
        )

        response = format_dns_forwarded_vs_cached_summary_response(
            metrics,
            time_range
        )

        return response, updated_context

    if intent == "dns_forwarded_count":
        time_range = parsed_query["time_range"]

        forwarded = influx_client.get_dns_forwarded_count(
            time_range=time_range
        )

        response = format_dns_forwarded_count_response(
            forwarded,
            time_range
        )

        return response, updated_context

    if intent == "dns_cached_count":
        time_range = parsed_query["time_range"]

        cached = influx_client.get_dns_cached_count(
            time_range=time_range
        )

        response = format_dns_cached_count_response(
            cached,
            time_range
        )

        return response, updated_context

    # Disk queries
    if intent == "disk_used_pct":
        host = parsed_query["host"]

        disk_metrics = (
            influx_client.get_current_disk_metrics(host)
        )

        response = format_disk_used_pct_response(
            host,
            disk_metrics
        )

        return response, updated_context

    if intent == "disk_status":
        host = parsed_query["host"]

        disk_metrics = (
            influx_client.get_current_disk_metrics(host)
        )

        response = format_disk_status_response(
            host,
            disk_metrics
        )

        return response, updated_context

    if intent == "disk_compare_hosts":
        hosts = parsed_query["hosts"]
        compare_mode = parsed_query.get(
            "compare_mode",
            "max"
        )

        disk_metrics = (
            influx_client.get_multiple_disk_metrics(hosts)
        )

        response = format_disk_compare_response(
            disk_metrics,
            compare_mode=compare_mode
        )

        return response, updated_context

    return (
        "Intención reconocida pero no implementada todavía.",
        updated_context
    )