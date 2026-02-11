import requests
from src.utils.logger import get_logger


def get_cpu_info(ip: str, auth: dict) -> dict:
    """Retrieve CPU information from a network switch.

    Args:
        ip: IP address of the switch
        auth: Authentication details containing 'tid' and 'userLvl'

    Returns:
        dict: JSON response with CPU information or error dict
    """

    logger = get_logger(__name__)
    logger.debug(f"Retrieving CPU info from switch at {ip}")

    if "error" in auth:
        logger.error(f"Authentication failed for switch at {ip}: {auth['error']}")
        return {"error": "Authentication failed"}

    url = f"http://{ip}/data/cpuInfo.json"
    params = {
        "_tid_": auth["_tid_"],
        "usrLvl": str(auth["usrLvl"]),
    }
    payload = {"unit": "unit1"}

    try:
        response = requests.post(url, json=payload, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully retrieved CPU info from {ip}")
        return data
    except requests.RequestException as e:
        logger.error(
            f"Failed to retrieve CPU info from switch at {ip}: {e}", exc_info=True
        )
        return {"error": str(e)}
