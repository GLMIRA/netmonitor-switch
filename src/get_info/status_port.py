import requests
from src.utils.logger import get_logger


def get_status_port(ip: str, auth: dict) -> dict:
    """Retrieve port status information from a network switch.

    Args:
        ip: IP address of the switch
        auth: Authentication details containing 'tid' and 'userLvl'

    Returns:
        dict: JSON response with port status information or error dict
    """

    logger = get_logger(__name__)
    logger.debug(f"Retrieving port status from switch at {ip}")

    if "error" in auth:
        logger.error(f"Authentication failed for switch at {ip}: {auth['error']}")
        return {"error": "Authentication failed"}

    url = f"http://{ip}/data/portStatusCfg.json"
    params = {
        "_tid_": auth["_tid_"],
        "usrLvl": str(auth["usrLvl"]),
    }
    payload = {
        "operation": "load",
        "special": "display",
        "tab": "unit1",
    }

    try:
        response = requests.post(url, json=payload, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully retrieved port status from {ip}")
        return data
    except requests.RequestException as e:
        logger.error(
            f"Failed to retrieve port status from switch at {ip}: {e}", exc_info=True
        )
        return {"error": str(e)}
