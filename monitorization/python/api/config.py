import os

# Pi-hole
PIHOLE_URL = os.getenv("PIHOLE_URL", "http://localhost")
PIHOLE_PASSWORD = os.getenv("PIHOLE_PASSWORD", "")

# InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "TFG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "pihole_metrics")

# Runtime state
STATE_FILE = os.getenv("STATE_FILE", "last_timestamp.txt")