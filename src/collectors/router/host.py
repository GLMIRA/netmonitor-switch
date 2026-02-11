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
        host_info = session.get(f"http://{router_ip}/api/system/HostInfo", timeout=5)
        json_data = host_info.json()
        logger.debug(f"Host info response: {json_data}")
        return json_data
    except Exception as e:
        logger.error(f"Error collecting host info: {e}")
        return {"error": str(e)}
