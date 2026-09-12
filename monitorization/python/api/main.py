from pihole_client import get_sid, get_queries
from state import load_last_timestamp, save_last_timestamp

from influx_writer import (
    write_total_to_influx,
    write_client_metrics_to_influx,
    write_query_types_to_influx,
    write_top_domains_to_influx,
    write_ip_version_to_influx,
    write_forwarded_to_influx,
    write_cached_to_influx
)

from metrics_calculator import (
    filter_new_queries,
    calculate_total,
    calculate_blocked,
    calculate_qps,
    calculate_blocked_percentage,
    calculate_active_clients,
    calculate_client_metrics,
    calculate_query_types,
    calculate_top_domains,
    calculate_ip_version,
    calculate_forwarded,
    calculate_cached,
    calculate_cached_percentage
)


def main():
    # Authenticate with Pi-hole and load the last processed timestamp
    sid = get_sid()
    last_timestamp = load_last_timestamp()

    # Retrieve queries and keep only the ones that have not been processed yet
    queries = get_queries(sid)
    new_queries = filter_new_queries(queries, last_timestamp)

    # Calculate global and client metrics
    total = calculate_total(new_queries)
    blocked = calculate_blocked(new_queries)
    blocked_pct = calculate_blocked_percentage(blocked, total)

    active_clients = calculate_active_clients(new_queries)
    client_metrics = calculate_client_metrics(new_queries)

    query_types = calculate_query_types(new_queries)
    top_domains = calculate_top_domains(new_queries)
    ip_versions = calculate_ip_version(new_queries)

    forwarded = calculate_forwarded(new_queries)
    cached = calculate_cached(new_queries)
    cached_pct = calculate_cached_percentage(cached, total)

    qps = calculate_qps(total, 300)

    # Show the calculated metrics in the console
    print("\n--- GLOBAL METRICS ---")
    print(f"Total queries: {total}")
    print(f"QPS: {qps:.2f}")
    print(f"Blocked: {blocked} ({blocked_pct:.2f}%)")
    print(f"Cached: {cached} ({cached_pct:.2f}%)")
    print(f"Forwarded: {forwarded}")
    print(f"Active clients: {active_clients}")

    print("\n--- CLIENT METRICS ---")
    for ip, stats in client_metrics.items():
        print(
            f"{ip} → "
            f"Q:{stats['queries']} | "
            f"B:{stats['blocked']} ({stats['blocked_pct']:.1f}%) | "
            f"C:{stats['cached']} ({stats['cached_pct']:.1f}%) | "
            f"F:{stats['forwarded']}"
        )

    print("\n")

    # Save the timestamp of the latest query processed
    if new_queries:
        max_timestamp = max(q["time"] for q in new_queries)
        save_last_timestamp(max_timestamp)

    # Store all calculated metrics in InfluxDB
    write_total_to_influx(
        total,
        qps,
        blocked,
        blocked_pct,
        active_clients,
        cached_pct
    )
    write_client_metrics_to_influx(client_metrics)
    write_query_types_to_influx(query_types)
    write_top_domains_to_influx(top_domains)
    write_ip_version_to_influx(ip_versions)
    write_forwarded_to_influx(forwarded)
    write_cached_to_influx(cached)


if __name__ == "__main__":
    main()