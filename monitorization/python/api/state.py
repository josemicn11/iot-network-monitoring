import os

from config import STATE_FILE


def load_last_timestamp():
    # Load the timestamp of the last processed query
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return float(f.read().strip())

    return 0.0


def save_last_timestamp(ts):
    # Save the timestamp of the latest processed query
    with open(STATE_FILE, "w") as f:
        f.write(str(ts))