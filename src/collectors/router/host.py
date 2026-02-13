import requests
from src.utils.logger import get_logger


logger = get_logger(__name__)


def collect_host_info(router_ip: str, session: requests.Session) -> dict:
    """Coleta informações do host do roteador.

    Args:
        router_ip: IP do roteador
        session: sessão autenticada

    Returns:
        dict: Informações coletadas do host
    """

    logger.info(f"Collecting host info from router {router_ip}")
    try:
        url = f"http://{router_ip}/api/system/HostInfo"
        logger.debug(f"Requesting URL: {url}")
        logger.debug(f"Session cookies: {session.cookies.get_dict()}")

        host_info = session.get(url, timeout=5)
        logger.debug(f"Response status code: {host_info.status_code}")
        logger.debug(f"Response headers: {dict(host_info.headers)}")
        logger.debug(f"Response content (first 200 chars): {host_info.text[:200]}")

        host_info.raise_for_status()
        json_data = host_info.json()
        logger.debug(f"Host info response: {json_data}")
        return json_data
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTP error collecting host info: {e} - Status: {host_info.status_code}"
        )
        return {"error": str(e)}
    except requests.exceptions.JSONDecodeError as e:
        logger.error(
            f"JSON decode error collecting host info: {e} - Response text: {host_info.text[:500]}"
        )
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error collecting host info: {e}")
        return {"error": str(e)}
