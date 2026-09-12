from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET


def write_total_to_influx(total, qps, blocked, blocked_pct, active_clients, cached_pct):
    # Store the general Pi-hole metrics in InfluxDB
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        point = (
            Point("pihole_api")
            .field("total", float(total))
            .field("qps", float(qps))
            .field("blocked", float(blocked))
            .field("blocked_pct", float(blocked_pct))
            .field("active_clients", float(active_clients))
            .field("cached_pct", float(cached_pct))
            .time(datetime.utcnow(), WritePrecision.NS)
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_client_metrics_to_influx(client_metrics):
    # Store the metrics calculated for each active client
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        for client_ip, stats in client_metrics.items():

            point = (
                Point("pihole_clients")
                .tag("client", client_ip)
                .field("queries", float(stats["queries"]))
                .field("blocked", float(stats["blocked"]))
                .field("cached", float(stats["cached"]))
                .field("forwarded", float(stats["forwarded"]))
                .field("blocked_pct", float(stats["blocked_pct"]))
                .field("cached_pct", float(stats["cached_pct"]))
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_query_types_to_influx(query_types):
    # Store the number of queries for each DNS query type
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        for qtype, count in query_types.items():

            point = (
                Point("pihole_query_types")
                .tag("type", qtype)
                .field("count", float(count))
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_top_domains_to_influx(top_domains):
    # Store the most frequently requested domains
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        for domain, count in top_domains.items():

            point = (
                Point("pihole_top_domains")
                .tag("domain", domain)
                .field("count", float(count))
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_ip_version_to_influx(ip_versions):
    # Store the number of IPv4 and IPv6 queries
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        for version, count in ip_versions.items():

            point = (
                Point("pihole_ip_versions")
                .tag("version", version)
                .field("count", float(count))
                .time(datetime.utcnow(), WritePrecision.NS)
            )

            write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_forwarded_to_influx(forwarded):
    # Store the number of queries forwarded to upstream DNS servers
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        point = (
            Point("pihole_forwarded")
            .field("count", float(forwarded))
            .time(datetime.utcnow(), WritePrecision.NS)
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_cached_to_influx(cached):
    # Store the number of queries answered from the Pi-hole cache
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        write_api = client.write_api(write_options=SYNCHRONOUS)

        point = (
            Point("pihole_cached")
            .field("count", float(cached))
            .time(datetime.utcnow(), WritePrecision.NS)
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)