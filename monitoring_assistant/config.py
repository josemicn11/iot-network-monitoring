import os

# InfluxDB configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "TFG")
INFLUX_BUCKET = os.getenv("SYSTEM_INFLUX_BUCKET", "system_metrics")
PIHOLE_BUCKET = os.getenv("INFLUX_BUCKET", "pihole_metrics")

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Ollama configuration
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma4:e2b"
)