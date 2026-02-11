"""Processor for WAN connection data from router.

This module processes WAN/Internet connection information from the Huawei
router, extracting connection status, IP configuration, bandwidth metrics,
and network performance data.
"""

from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Connection status constants
CONNECTION_STATUS_CONNECTED = "Connected"
CONNECTION_STATUS_DISCONNECTED = "Disconnected"

# Access status constants
ACCESS_STATUS_UP = "Up"
ACCESS_STATUS_DOWN = "Down"

# Default values
DEFAULT_BANDWIDTH = 0
DEFAULT_DNS_SERVERS = ""

# Conversion constants
KILOBITS_TO_MEGABITS = 1000


def process_wan_status(wan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WAN connection status and configuration.

    Extracts connection status, IP addresses, DNS configuration, and
    PPPoE details from WAN API response.

    Args:
        wan_data: Response dictionary from /api/ntwk/wan?type=active endpoint.

    Returns:
        Dictionary containing processed WAN status with the following keys:
            - connection_status: Connection state (str)
            - ipv6_connection_status: IPv6 connection state (str)
            - access_status: Physical link status (str)
            - is_connected: Boolean connection status (bool)
            - interface_enabled: Interface enabled status (bool)
            - interface_name: WAN interface name (str)
            - interface_alias: Interface alias (str)
            - ipv4_address: Public IPv4 address (str)
            - ipv4_gateway: ISP gateway address (str)
            - ipv4_mask: Network mask (str)
            - ipv6_address: Public IPv6 address without prefix (str)
            - ipv6_address_full: IPv6 address with prefix (str)
            - ipv6_prefix_length: IPv6 prefix length (int)
            - ipv6_gateway: IPv6 gateway (str)
            - ipv6_prefix_list: IPv6 prefix delegation (str)
            - ipv4_dns_servers: IPv4 DNS servers (str)
            - ipv6_dns_servers: IPv6 DNS servers (str)
            - pppoe_username: PPPoE username (str)
            - pppoe_ac_name: PPPoE access concentrator (str)
            - pppoe_service_name: PPPoE service name (str)
            - pppoe_trigger: PPPoE dial trigger mode (str)
            - connection_type: Connection type (str)
            - wan_type: WAN configuration type (str)
            - service_list: Configured services (str)
            - ipv4_enabled: IPv4 enabled status (bool)
            - ipv6_enabled: IPv6 enabled status (bool)
            - nat_type: NAT type (int)
            - mtu: Maximum transmission unit (int)
            - mru: Maximum receive unit (int)
            - error: Error message if processing failed (str, optional)

    Example:
        >>> wan_data = {"ConnectionStatus": "Connected", ...}
        >>> status = process_wan_status(wan_data)
        >>> print(status['is_connected'])
        True
    """
    try:
        if "error" in wan_data:
            return _create_error_status(wan_data["error"])

        connection_status = wan_data.get("ConnectionStatus", "")
        ipv6_connection_status = wan_data.get("IPv6ConnectionStatus", "")
        access_status = wan_data.get("AccessStatus", "")

        # Parse IPv6 address (format: "2804:23b0:8002:d92:7509:b950:e645:3337/64")
        ipv6_address_full = wan_data.get("IPv6Addr", "")
        ipv6_address, ipv6_prefix_length = _parse_ipv6_address(ipv6_address_full)

        status = {
            # Connection status
            "connection_status": connection_status,
            "ipv6_connection_status": ipv6_connection_status,
            "access_status": access_status,
            "is_connected": _is_connected(connection_status, access_status),
            "interface_enabled": wan_data.get("Enable", False),
            "interface_name": wan_data.get("Name", ""),
            "interface_alias": wan_data.get("Alias", ""),
            # IPv4 configuration
            "ipv4_address": wan_data.get("IPv4Addr", ""),
            "ipv4_gateway": wan_data.get("IPv4Gateway", ""),
            "ipv4_mask": wan_data.get("IPv4Mask", ""),
            # IPv6 configuration
            "ipv6_address": ipv6_address,
            "ipv6_address_full": ipv6_address_full,
            "ipv6_prefix_length": ipv6_prefix_length,
            "ipv6_gateway": wan_data.get("IPv6Gateway", ""),
            "ipv6_prefix_list": wan_data.get("IPv6PrefixList", ""),
            # DNS servers
            "ipv4_dns_servers": wan_data.get("IPv4DnsServers", DEFAULT_DNS_SERVERS),
            "ipv6_dns_servers": wan_data.get("IPv6DnsServers", DEFAULT_DNS_SERVERS),
            # PPPoE details
            "pppoe_username": wan_data.get("Username", ""),
            "pppoe_ac_name": wan_data.get("PPPoEACName", ""),
            "pppoe_service_name": wan_data.get("PPPoEServiceName", ""),
            "pppoe_trigger": wan_data.get("PPPTrigger", ""),
            # Connection configuration
            "connection_type": wan_data.get("ConnectionType", ""),
            "wan_type": wan_data.get("WanType", ""),
            "service_list": wan_data.get("ServiceList", ""),
            "ipv4_enabled": wan_data.get("IPv4Enable", False),
            "ipv6_enabled": wan_data.get("IPv6Enable", False),
            "nat_type": wan_data.get("NATType", 0),
            "mtu": wan_data.get("MTU", 0),
            "mru": wan_data.get("MRU", 0),
        }

        logger.debug(
            f"WAN status processed: {status['connection_status']}, "
            f"IPv4: {status['ipv4_address']}, IPv6: {ipv6_address}"
        )
        return status

    except Exception as error:
        logger.error(f"Error processing WAN status: {error}", exc_info=True)
        return _create_error_status(str(error))


def process_wan_bandwidth(wan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WAN bandwidth metrics and history.

    Extracts current bandwidth usage, maximum recorded bandwidth,
    and bandwidth history from WAN API response.

    Args:
        wan_data: Response dictionary from /api/ntwk/wan?type=active endpoint.

    Returns:
        Dictionary containing bandwidth metrics with the following keys:
            - upload_current_kbps: Current upload speed in Kbps (int)
            - download_current_kbps: Current download speed in Kbps (int)
            - upload_current_mbps: Current upload speed in Mbps (float)
            - download_current_mbps: Current download speed in Mbps (float)
            - upload_max_kbps: Maximum upload speed recorded (int)
            - download_max_kbps: Maximum download speed recorded (int)
            - upload_max_mbps: Maximum upload in Mbps (float)
            - download_max_mbps: Maximum download in Mbps (float)
            - upload_history: List of upload bandwidth samples (list)
            - download_history: List of download bandwidth samples (list)
            - bandwidth_timestamps: List of timestamp samples (list)
            - error: Error message if processing failed (str, optional)

    Example:
        >>> wan_data = {"UpBandwidth": 1000, "DownBandwidth": 5000, ...}
        >>> bandwidth = process_wan_bandwidth(wan_data)
        >>> print(bandwidth['download_current_mbps'])
        5.0
    """
    try:
        if "error" in wan_data:
            return _create_error_bandwidth(wan_data["error"])

        upload_current = wan_data.get("UpBandwidth", DEFAULT_BANDWIDTH)
        download_current = wan_data.get("DownBandwidth", DEFAULT_BANDWIDTH)
        upload_max = wan_data.get("UpBandwidthMax", DEFAULT_BANDWIDTH)
        download_max = wan_data.get("DownBandwidthMax", DEFAULT_BANDWIDTH)

        bandwidth = {
            # Current bandwidth
            "upload_current_kbps": upload_current,
            "download_current_kbps": download_current,
            "upload_current_mbps": round(upload_current / KILOBITS_TO_MEGABITS, 2),
            "download_current_mbps": round(download_current / KILOBITS_TO_MEGABITS, 2),
            # Maximum bandwidth recorded
            "upload_max_kbps": upload_max,
            "download_max_kbps": download_max,
            "upload_max_mbps": round(upload_max / KILOBITS_TO_MEGABITS, 2),
            "download_max_mbps": round(download_max / KILOBITS_TO_MEGABITS, 2),
            # Bandwidth history
            "upload_history": _parse_bandwidth_history(
                wan_data.get("UpBandwidthHistory", "")
            ),
            "download_history": _parse_bandwidth_history(
                wan_data.get("DownBandwidthHistory", "")
            ),
            "bandwidth_timestamps": _parse_bandwidth_timestamps(
                wan_data.get("BandwidthTime", "")
            ),
        }

        logger.debug(
            f"Bandwidth processed: UP {bandwidth['upload_current_mbps']} Mbps, "
            f"DOWN {bandwidth['download_current_mbps']} Mbps"
        )
        return bandwidth

    except Exception as error:
        logger.error(f"Error processing WAN bandwidth: {error}", exc_info=True)
        return _create_error_bandwidth(str(error))


def _is_connected(connection_status: str, access_status: str) -> bool:
    """Determine if WAN connection is fully established.

    Args:
        connection_status: PPPoE connection status.
        access_status: Physical link status.

    Returns:
        True if both connection and access are up, False otherwise.
    """
    return (
        connection_status == CONNECTION_STATUS_CONNECTED
        and access_status == ACCESS_STATUS_UP
    )


def _parse_bandwidth_history(history_string: str) -> List[int]:
    """Parse bandwidth history string into list of integers.

    Args:
        history_string: Comma-separated bandwidth values.

    Returns:
        List of bandwidth values as integers. Empty list on parse error.
    """
    if not history_string:
        return []

    try:
        return [int(value) for value in history_string.split(",")]
    except (ValueError, AttributeError) as error:
        logger.debug(f"Error parsing bandwidth history: {error}")
        return []


def _parse_bandwidth_timestamps(timestamp_string: str) -> List[int]:
    """Parse bandwidth timestamp string into list of integers.

    Args:
        timestamp_string: Comma-separated timestamp values.

    Returns:
        List of timestamps as integers. Empty list on parse error.
    """
    if not timestamp_string:
        return []

    try:
        return [int(value) for value in timestamp_string.split(",")]
    except (ValueError, AttributeError) as error:
        logger.debug(f"Error parsing bandwidth timestamps: {error}")
        return []


def _parse_ipv6_address(ipv6_full: str) -> tuple[str, int]:
    """Parse IPv6 address with prefix length.

    Splits IPv6 address from format "2804:23b0:8002:d92::1/64" into
    address and prefix length components.

    Args:
        ipv6_full: IPv6 address string, optionally with /prefix.

    Returns:
        Tuple of (ipv6_address, prefix_length). Returns ("", 0) on error.
    """
    if not ipv6_full:
        return ("", 0)

    try:
        if "/" in ipv6_full:
            address, prefix = ipv6_full.split("/", 1)
            return (address.strip(), int(prefix))
        else:
            return (ipv6_full.strip(), 0)
    except (ValueError, AttributeError) as error:
        logger.debug(f"Error parsing IPv6 address '{ipv6_full}': {error}")
        return ("", 0)


def _create_error_status(error_message: str) -> Dict[str, Any]:
    """Create error status dictionary.

    Args:
        error_message: Error description.

    Returns:
        Status dictionary with error field and default values.
    """
    return {
        "connection_status": "",
        "ipv6_connection_status": "",
        "access_status": "",
        "is_connected": False,
        "interface_enabled": False,
        "interface_name": "",
        "interface_alias": "",
        "ipv4_address": "",
        "ipv4_gateway": "",
        "ipv4_mask": "",
        "ipv6_address": "",
        "ipv6_address_full": "",
        "ipv6_prefix_length": 0,
        "ipv6_gateway": "",
        "ipv6_prefix_list": "",
        "ipv4_dns_servers": "",
        "ipv6_dns_servers": "",
        "pppoe_username": "",
        "pppoe_ac_name": "",
        "pppoe_service_name": "",
        "pppoe_trigger": "",
        "connection_type": "",
        "wan_type": "",
        "service_list": "",
        "ipv4_enabled": False,
        "ipv6_enabled": False,
        "nat_type": 0,
        "mtu": 0,
        "mru": 0,
        "error": error_message,
    }


def _create_error_bandwidth(error_message: str) -> Dict[str, Any]:
    """Create error bandwidth dictionary.

    Args:
        error_message: Error description.

    Returns:
        Bandwidth dictionary with error field and default values.
    """
    return {
        "upload_current_kbps": 0,
        "download_current_kbps": 0,
        "upload_current_mbps": 0.0,
        "download_current_mbps": 0.0,
        "upload_max_kbps": 0,
        "download_max_kbps": 0,
        "upload_max_mbps": 0.0,
        "download_max_mbps": 0.0,
        "upload_history": [],
        "download_history": [],
        "bandwidth_timestamps": [],
        "error": error_message,
    }
