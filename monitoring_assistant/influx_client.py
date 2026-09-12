from influxdb_client import InfluxDBClient

from config import (
    INFLUX_URL,
    INFLUX_TOKEN,
    INFLUX_ORG,
    INFLUX_BUCKET,
    PIHOLE_BUCKET
)


DISK_DEVICE_BY_HOST = {
    "raspberry": "mmcblk1p3",
    "ASUS_Josemi": "C:",
}


class MonitoringInfluxClient:
    def __init__(self):
        # Create the connection with InfluxDB
        self.client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        self.query_api = self.client.query_api()

    def _extract_single_value(self, tables):
        # Return the first value found in an InfluxDB query result
        for table in tables:
            for record in table.records:
                return record.get_value()

        return None

    def _time_range_to_flux_start(self, time_range: str) -> str:
        # Convert the time range received from the assistant to Flux format
        if time_range == "today":
            return "today()"

        if isinstance(time_range, str) and time_range.startswith("-"):
            return time_range

        if time_range == "now":
            return "-10m"

        return "-6h"

    def get_current_load1(self, host: str):
        # Get the latest system load value for a host
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "system")
        |> filter(fn: (r) => r["host"] == "{host}")
        |> filter(fn: (r) => r._field == "load1")
        |> last()
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_current_ram_used_percent(self, host: str):
        # Get the latest RAM usage percentage
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "mem")
        |> filter(fn: (r) => r["host"] == "{host}")
        |> filter(fn: (r) => r._field == "used_percent")
        |> last()
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_current_disk_used_percent(self, host: str):
        # Get the disk associated with the host before querying its usage
        device = DISK_DEVICE_BY_HOST.get(host)

        if not device:
            return None

        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "disk")
        |> filter(fn: (r) => r["host"] == "{host}")
        |> filter(fn: (r) => r._field == "used_percent")
        |> filter(fn: (r) => r["device"] == "{device}")
        |> last()
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_current_disk_metrics(self, host: str):
        # Return the current disk metrics for one host
        used_percent = self.get_current_disk_used_percent(host)

        return {
            "used_percent": used_percent,
        }

    def get_multiple_disk_metrics(self, hosts: list):
        # Get disk metrics for several hosts
        results = {}

        for host in hosts:
            results[host] = self.get_current_disk_metrics(host)

        return results

    def get_host_status_metrics(self, host: str):
        # Get the main system metrics used to determine the host status
        return {
            "load1": self.get_current_load1(host),
            "ram_used_percent": self.get_current_ram_used_percent(host),
            "disk_used_percent": self.get_current_disk_used_percent(host),
        }

    def get_multiple_current_load1(self, hosts: list):
        # Get the current system load for several hosts
        results = {}

        for host in hosts:
            results[host] = self.get_current_load1(host)

        return results

    def get_top_domains(self, time_range: str = "-6h", limit_n: int = 10):
        # Get the most queried domains during the selected period
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_top_domains")
        |> filter(fn: (r) => r._field == "count")
        |> group(columns: ["domain"])
        |> sum(column: "_value")
        |> group()
        |> sort(columns: ["_value"], desc: true)
        |> limit(n: {limit_n})
        '''

        tables = self.query_api.query(query)

        results = []

        for table in tables:
            for record in table.records:
                results.append({
                    "domain": record.values.get("domain"),
                    "count": record.get_value(),
                })

        return results

    def get_dns_domain_query_count(self, domain: str, time_range: str = "-6h") -> int:
        # Count how many times a specific domain was queried
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_top_domains")
        |> filter(fn: (r) => r._field == "count")
        |> filter(fn: (r) => r["domain"] == "{domain}")
        |> sum(column: "_value")
        '''

        tables = self.query_api.query(query)

        total = 0

        for table in tables:
            for record in table.records:
                value = record.get_value()

                if value is not None:
                    total = int(value)

        return total

    def get_top_clients(self, time_range: str = "-6h", limit_n: int = 10):
        # Get the clients that generated the highest number of DNS queries
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_clients")
        |> filter(fn: (r) => r._field == "queries")
        |> group(columns: ["client"])
        |> sum()
        |> group()
        |> keep(columns: ["client", "_value"])
        |> sort(columns: ["_value"], desc: true)
        |> limit(n: {limit_n})
        '''

        tables = self.query_api.query(query)

        results = []

        for table in tables:
            for record in table.records:
                results.append({
                    "client": record.values.get("client"),
                    "count": record.get_value(),
                })

        return results

    def get_active_clients_list(self, time_range: str = "-6h"):
        # Get the list of clients that generated DNS queries
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_clients")
        |> filter(fn: (r) => r._field == "queries")
        |> keep(columns: ["client"])
        |> group()
        |> distinct(column: "client")
        '''

        tables = self.query_api.query(query)

        results = []

        for table in tables:
            for record in table.records:
                client = record.get_value()

                if client is not None:
                    results.append(client)

        return sorted(set(results))

    def _get_last_metric_value(self, measurement: str, field: str, time_range: str):
        # Get the latest value of a DNS metric
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        |> last()
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def _get_mean_metric_value(self, measurement: str, field: str, time_range: str):
        # Calculate the mean value of a DNS metric
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        |> mean(column: "_value")
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_dns_total_queries(self, time_range: str = "-6h"):
        # Get the total number of DNS queries during the selected period
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_api")
        |> filter(fn: (r) => r._field == "total")
        |> sum(column: "_value")
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_dns_qps(self, time_range: str = "-6h"):
        return self._get_mean_metric_value("pihole_api", "qps", time_range)

    def get_dns_blocked_pct(self, time_range: str = "-6h"):
        return self._get_mean_metric_value("pihole_api", "blocked_pct", time_range)

    def get_dns_cached_pct(self, time_range: str = "-6h"):
        return self._get_mean_metric_value("pihole_api", "cached_pct", time_range)

    def get_dns_active_clients_count(self, time_range: str = "-6h"):
        return self._get_last_metric_value("pihole_api", "active_clients", time_range)

    def get_dns_summary_metrics(self, time_range: str = "-6h"):
        # Group the main DNS metrics in a single response
        return {
            "total_queries": self.get_dns_total_queries(time_range),
            "qps": self.get_dns_qps(time_range),
            "blocked_pct": self.get_dns_blocked_pct(time_range),
            "cached_pct": self.get_dns_cached_pct(time_range),
            "active_clients": self.get_dns_active_clients_count(time_range),
        }

    def get_dns_query_types_summary(self, time_range: str = "-6h", limit_n: int = 5):
        # Get the most common DNS query types
        range_start = self._time_range_to_flux_start(time_range)

        limit_clause = f'|> limit(n: {limit_n})' if limit_n is not None else ""

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_query_types")
        |> filter(fn: (r) => r._field == "count")
        |> group(columns: ["type"])
        |> sum()
        |> group()
        |> sort(columns: ["_value"], desc: true)
        |> keep(columns: ["type", "_value"])
        {limit_clause}
        '''

        tables = self.query_api.query(query)

        results = []

        for table in tables:
            for record in table.records:
                results.append({
                    "type": record.values.get("type"),
                    "count": record.get_value(),
                })

        return results

    def get_dns_query_type_count(self, query_type: str, time_range: str = "-6h") -> int:
        # Count the number of queries for a specific DNS query type
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "pihole_query_types")
        |> filter(fn: (r) => r._field == "count")
        |> filter(fn: (r) => r["type"] == "{query_type}")
        |> sum(column: "_value")
        '''

        tables = self.query_api.query(query)

        total = 0

        for table in tables:
            for record in table.records:
                value = record.get_value()

                if value is not None:
                    total = int(value)

        return total

    def _get_sum_metric_value(self, measurement: str, field: str, time_range: str):
        # Get the accumulated value of a DNS metric
        range_start = self._time_range_to_flux_start(time_range)

        query = f'''
        from(bucket: "{PIHOLE_BUCKET}")
        |> range(start: {range_start})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        |> sum(column: "_value")
        '''

        tables = self.query_api.query(query)
        return self._extract_single_value(tables)

    def get_dns_forwarded_count(self, time_range: str = "-6h"):
        return self._get_sum_metric_value("pihole_forwarded", "count", time_range)

    def get_dns_cached_count(self, time_range: str = "-6h"):
        return self._get_sum_metric_value("pihole_cached", "count", time_range)

    def get_dns_forwarded_vs_cached_metrics(self, time_range: str = "-6h"):
        # Return forwarded and cached DNS queries together
        return {
            "forwarded": self.get_dns_forwarded_count(time_range),
            "cached": self.get_dns_cached_count(time_range),
        }

    def get_current_ram_metrics(self, host: str):
        # Get the latest RAM values and convert bytes to GB when needed
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "mem")
        |> filter(fn: (r) => r["host"] == "{host}")
        |> filter(fn: (r) => r._field == "total" or r._field == "available" or r._field == "used" or r._field == "used_percent")
        |> last()
        '''

        tables = self.query_api.query(query)

        results = {
            "total": None,
            "available": None,
            "used": None,
            "used_percent": None,
        }

        for table in tables:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()

                if field in ["total", "available", "used"] and value is not None:
                    results[field] = float(value) / 1073741824.0

                elif field == "used_percent" and value is not None:
                    results[field] = float(value)

        return results

    def get_multiple_ram_metrics(self, hosts: list):
        # Get RAM metrics for several hosts
        results = {}

        for host in hosts:
            results[host] = self.get_current_ram_metrics(host)

        return results

    def close(self):
        # Close the InfluxDB client connection
        self.client.close()