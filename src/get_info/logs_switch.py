import requests
from src.utils.logger import get_logger


def get_logs_switch(ip: str, auth: dict) -> dict:
    """Retrieve logs information from a network switch.

    Args:
        ip: IP address of the switch
        auth: Authentication details containing 'tid' and 'userLvl'

    Returns:
        dict: JSON response with logs information or error dict
    """

    logger = get_logger(__name__)
    logger.debug(f"Retrieving logs from switch at {ip}")

    if "error" in auth:
        logger.error(f"Authentication failed for switch at {ip}: {auth['error']}")
        return {"error": "Authentication failed"}

    url = f"http://{ip}/data/logtable.json"
    headers = {
        "_tid_": auth["_tid_"],
        "usrLvl": str(auth["usrLvl"]),
    }
    payload = {"operation": "load"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(
            f"Successfully retrieved {len(data.get('data', []))} logs from {ip}"
        )
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to retrieve logs from switch at {ip}: {e}", exc_info=True)
        return {"error": str(e)}
