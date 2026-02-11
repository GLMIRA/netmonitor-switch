"""Collector for WAN connection information from router.

This module collects WAN/Internet connection data from the Huawei router,
including connection status, IP addresses, bandwidth metrics, and PPPoE
configuration.
"""

import requests
from src.utils.logger import get_logger

logger = get_logger(__name__)

# API endpoint constants
WAN_ENDPOINT = "/api/ntwk/wan"
WAN_QUERY_PARAM_TYPE = "type"
WAN_QUERY_PARAM_VALUE = "active"

# Request timeout
REQUEST_TIMEOUT_SECONDS = 5


def collect_wan_info(router_ip: str, session: requests.Session) -> dict:
    """Collect WAN connection information from router.

    Retrieves active WAN connection data including connection status,
    IP configuration, bandwidth metrics, DNS servers, and PPPoE details.

    Args:
        router_ip: IP address of the router.
        session: Authenticated session object with valid cookies.

    Returns:
        Dictionary containing WAN connection data from API response.
        On error, returns dict with 'error' key containing error message.

    Example:
        >>> session = get_authenticated_session("192.168.3.1", "admin", "pass")
        >>> wan_data = collect_wan_info("192.168.3.1", session)
        >>> print(wan_data['ConnectionStatus'])
        'Connected'
    """
    logger.info(f"Collecting WAN info from router {router_ip}")

    try:
        url = _build_wan_endpoint_url(router_ip)
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        wan_data = response.json()
        logger.debug(
            f"WAN info collected successfully: {wan_data.get('ConnectionStatus')}"
        )

        return wan_data

    except requests.exceptions.Timeout as error:
        logger.error(f"Timeout collecting WAN info from {router_ip}: {error}")
        return {"error": f"Request timeout: {error}"}

    except requests.exceptions.RequestException as error:
        logger.error(f"Request error collecting WAN info: {error}")
        return {"error": f"Request failed: {error}"}

    except ValueError as error:
        logger.error(f"Invalid JSON response from WAN endpoint: {error}")
        return {"error": f"Invalid JSON response: {error}"}

    except Exception as error:
        logger.error(f"Unexpected error collecting WAN info: {error}", exc_info=True)
        return {"error": str(error)}


def _build_wan_endpoint_url(router_ip: str) -> str:
    """Build complete WAN endpoint URL with query parameters.

    Args:
        router_ip: IP address of the router.

    Returns:
        Complete URL string for WAN endpoint.
    """
    return (
        f"http://{router_ip}{WAN_ENDPOINT}"
        f"?{WAN_QUERY_PARAM_TYPE}={WAN_QUERY_PARAM_VALUE}"
    )
