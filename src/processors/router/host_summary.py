"""Processor for aggregated host metrics from router.

This module processes host information from the Huawei router API,
generating summary statistics about connected devices, network traffic,
and interface distribution.
"""

from typing import Dict, List, Any, Union
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Interface type constants
INTERFACE_TYPE_LAN = "LAN"
INTERFACE_TYPE_WIFI_2_4GHZ = "2.4GHz"
INTERFACE_TYPE_WIFI_5GHZ = "5GHz"

# Address source constants
ADDRESS_SOURCE_DHCP = "DHCP"
ADDRESS_SOURCE_STATIC = "STATIC"

# Conversion constants
KILOBYTES_TO_MEGABYTES = 1024


def process_host_summary(
    host_data: Union[List[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    """Process aggregated metrics from router hosts.

    Analyzes all hosts returned by the router API and generates summary
    statistics including device counts, interface distribution, IP assignment
    types, and total network traffic.

    Args:
        host_data: Response dictionary from /api/system/HostInfo endpoint.
                   Expected to contain a 'Hosts' key with list of host objects.

    Returns:
        Dictionary containing aggregated metrics with the following keys:
            - total_devices: Total number of hosts (int)
            - devices_online: Count of active devices (int)
            - devices_offline: Count of inactive devices (int)
            - devices_lan: Count of LAN-connected devices (int)
            - devices_wifi_2_4ghz: Count of 2.4GHz WiFi devices (int)
            - devices_wifi_5ghz: Count of 5GHz WiFi devices (int)
            - devices_dhcp: Count of DHCP-assigned devices (int)
            - devices_static: Count of static IP devices (int)
            - total_traffic_tx_kb: Total transmitted traffic in KB (int)
            - total_traffic_rx_kb: Total received traffic in KB (int)
            - total_traffic_tx_mb: Total transmitted traffic in MB (float)
            - total_traffic_rx_mb: Total received traffic in MB (float)
            - error: Error message if processing failed (str, optional)

    Example:
        >>> data = [{"Active": True, "InterfaceType": "LAN", ...}]
        >>> summary = process_host_summary(data)
        >>> print(summary['devices_online'])
        1
    """
    try:
        # Handle both list (API returns array directly) and dict with "Hosts" key
        if isinstance(host_data, list):
            hosts_list = host_data
        elif isinstance(host_data, dict):
            hosts_list = host_data.get("Hosts", [])
        else:
            hosts_list = []

        if not hosts_list:
            logger.warning("No hosts found in API response")
            return _create_empty_summary()

        counters = _initialize_counters()
        counters = _process_hosts(hosts_list, counters)
        summary = _build_summary_dict(counters, len(hosts_list))

        logger.debug(
            f"Processed host summary: {summary['devices_online']} online, "
            f"{summary['devices_offline']} offline, "
            f"{summary['total_traffic_rx_mb']} MB RX"
        )
        return summary

    except Exception as error:
        logger.error(f"Error processing host summary: {error}", exc_info=True)
        return _create_error_summary(str(error))


def _initialize_counters() -> Dict[str, int]:
    """Initialize all metric counters to zero.

    Returns:
        Dictionary with all counter keys initialized to 0.
    """
    return {
        "devices_online": 0,
        "devices_offline": 0,
        "devices_lan": 0,
        "devices_wifi_2_4ghz": 0,
        "devices_wifi_5ghz": 0,
        "devices_dhcp": 0,
        "devices_static": 0,
        "total_traffic_tx_kb": 0,
        "total_traffic_rx_kb": 0,
    }


def _process_hosts(
    hosts: List[Dict[str, Any]], counters: Dict[str, int]
) -> Dict[str, int]:
    """Process list of hosts and update counters.

    Args:
        hosts: List of host dictionaries from API response.
        counters: Counter dictionary to update.

    Returns:
        Updated counters dictionary.
    """
    for host in hosts:
        is_active = host.get("Active", False)

        _update_status_counters(counters, is_active)

        if is_active:
            _update_interface_counters(counters, host)
            _update_address_source_counters(counters, host)
            _update_traffic_counters(counters, host)

    return counters


def _update_status_counters(counters: Dict[str, int], is_active: bool) -> None:
    """Update online/offline device counters.

    Args:
        counters: Counter dictionary to update.
        is_active: Whether the device is currently active.
    """
    if is_active:
        counters["devices_online"] += 1
    else:
        counters["devices_offline"] += 1


def _update_interface_counters(counters: Dict[str, int], host: Dict[str, Any]) -> None:
    """Update interface type counters (LAN, WiFi 2.4GHz, WiFi 5GHz).

    Args:
        counters: Counter dictionary to update.
        host: Host data dictionary.
    """
    interface_type = host.get("InterfaceType", "")

    if interface_type == INTERFACE_TYPE_LAN:
        counters["devices_lan"] += 1
    elif interface_type == INTERFACE_TYPE_WIFI_2_4GHZ:
        counters["devices_wifi_2_4ghz"] += 1
    elif interface_type == INTERFACE_TYPE_WIFI_5GHZ:
        counters["devices_wifi_5ghz"] += 1


def _update_address_source_counters(
    counters: Dict[str, int], host: Dict[str, Any]
) -> None:
    """Update DHCP/Static IP counters.

    Args:
        counters: Counter dictionary to update.
        host: Host data dictionary.
    """
    address_source = host.get("AddressSource", "")

    if address_source == ADDRESS_SOURCE_DHCP:
        counters["devices_dhcp"] += 1
    elif address_source == ADDRESS_SOURCE_STATIC:
        counters["devices_static"] += 1


def _update_traffic_counters(counters: Dict[str, int], host: Dict[str, Any]) -> None:
    """Update network traffic counters (TX/RX).

    Args:
        counters: Counter dictionary to update.
        host: Host data dictionary.
    """
    try:
        transmitted_kb = int(host.get("TxKBytes", 0))
        received_kb = int(host.get("RxKBytes", 0))

        counters["total_traffic_tx_kb"] += transmitted_kb
        counters["total_traffic_rx_kb"] += received_kb
    except (ValueError, TypeError) as error:
        logger.debug(f"Invalid traffic data for host {host.get('MACAddress')}: {error}")


def _build_summary_dict(counters: Dict[str, int], total_devices: int) -> Dict[str, Any]:
    """Build final summary dictionary with calculated metrics.

    Args:
        counters: Processed counters dictionary.
        total_devices: Total number of devices.

    Returns:
        Complete summary dictionary.
    """
    return {
        "total_devices": total_devices,
        "devices_online": counters["devices_online"],
        "devices_offline": counters["devices_offline"],
        "devices_lan": counters["devices_lan"],
        "devices_wifi_2_4ghz": counters["devices_wifi_2_4ghz"],
        "devices_wifi_5ghz": counters["devices_wifi_5ghz"],
        "devices_dhcp": counters["devices_dhcp"],
        "devices_static": counters["devices_static"],
        "total_traffic_tx_kb": counters["total_traffic_tx_kb"],
        "total_traffic_rx_kb": counters["total_traffic_rx_kb"],
        "total_traffic_tx_mb": round(
            counters["total_traffic_tx_kb"] / KILOBYTES_TO_MEGABYTES, 2
        ),
        "total_traffic_rx_mb": round(
            counters["total_traffic_rx_kb"] / KILOBYTES_TO_MEGABYTES, 2
        ),
    }


def _create_empty_summary() -> Dict[str, int]:
    """Create summary with all values set to zero.

    Returns:
        Empty summary dictionary.
    """
    return {
        "total_devices": 0,
        "devices_online": 0,
        "devices_offline": 0,
        "devices_lan": 0,
        "devices_wifi_2_4ghz": 0,
        "devices_wifi_5ghz": 0,
        "devices_dhcp": 0,
        "devices_static": 0,
        "total_traffic_tx_kb": 0,
        "total_traffic_rx_kb": 0,
        "total_traffic_tx_mb": 0.0,
        "total_traffic_rx_mb": 0.0,
    }


def _create_error_summary(error_message: str) -> Dict[str, Any]:
    """Create error summary dictionary.

    Args:
        error_message: Error description.

    Returns:
        Summary dictionary with error field.
    """
    summary = _create_empty_summary()
    summary["error"] = error_message
    return summary
