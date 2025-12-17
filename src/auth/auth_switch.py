import requests
import ipaddress

from src.utils.logger import get_logger

logger = get_logger(__name__)


def switch_auth(
    ip: ipaddress.IPv4Address,
    username: str,
    password: str,
    operation: str,
) -> dict:
    """Authenticate to a network switch.

    Args:
        ip (STR): IP address
        username (STR): username
        password (STR): password
        operation (STR): operation

    Returns:
        dict: Response from the switch or error message
    """

    logger.debug(f"Authenticating to switch at {ip} with user {username}")

    url = f"http://{ip}/data/login.json"
    payload = {
        "username": username,
        "password": password,
        "operation": operation,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)
        if data.get("success") and "data" in data and data["data"]:
            logger.info(f"Successfully authenticated to switch at {ip}")
            return {
                "_tid_": data["data"]["_tid_"],
                "usrLvl": data["data"]["usrLvl"],
            }
        else:
            error_code = data.get("errorcode", "unknown")
            logger.error(
                f"Authentication failed for switch at {ip}: errorcode {error_code}"
            )
            return {"error": "Authentication failed"}

    except requests.RequestException as e:
        logger.error(f"Error authenticating to switch at {ip}: {e}")
        return {"error": str(e)}
