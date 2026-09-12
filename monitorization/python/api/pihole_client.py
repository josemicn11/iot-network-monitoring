import requests

from config import PIHOLE_URL, PIHOLE_PASSWORD


def get_sid():
    # Authenticate with Pi-hole and get the current session ID
    response = requests.post(
        f"{PIHOLE_URL}/api/auth",
        json={"password": PIHOLE_PASSWORD}
    )

    return response.json()["session"]["sid"]


def get_queries(sid, length=10000):
    # Get the latest DNS queries using the active Pi-hole session
    headers = {"X-FTL-SID": sid}

    response = requests.get(
        f"{PIHOLE_URL}/api/queries?length={length}&start=0&draw=1",
        headers=headers
    )

    return response.json().get("queries", [])