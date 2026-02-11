"""Processor for individual device information from router.

This module processes detailed information about each active device
connected to the Huawei router, including network metrics, connection
types, and device identification data.
"""

from typing import Dict, List, Any, Optional, Union
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Interface type constants
INTERFACE_TYPE_LAN = "LAN"
INTERFACE_TYPE_WIFI_2_4GHZ = "2.4GHz"
INTERFACE_TYPE_WIFI_5GHZ = "5GHz"

# Connection type constants
CONNECTION_TYPE_CABLE = "cable"
CONNECTION_TYPE_WIFI = "wifi"
CONNECTION_TYPE_UNKNOWN = "unknown"

# Default values
DEFAULT_HOSTNAME = "Unknown"
DEFAULT_LEASE_TIME = "0"

# Conversion constants
KILOBYTES_TO_MEGABYTES = 1024


def process_host_devices(
    host_data: Union[List[Dict[str, Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Process individual device information from router API.

    Filters and processes only active devices, extracting network metrics,
    connection details, and device identification information.

    Args:
        host_data: Response dictionary from /api/system/HostInfo endpoint.
                   Expected to contain a 'Hosts' key with list of host objects.

    Returns:
        List of dictionaries, each containing processed device information:
            - mac: MAC address (str)
            - ip: IPv4 address (str)
            - ipv6: IPv6 address (str)
            - hostname: Device hostname (str)
            - actual_name: Custom device name (str)
            - interface_type: LAN/2.4GHz/5GHz (str)
            - layer2_interface: Physical interface (str)
            - connection_type: cable/wifi/unknown (str)
            - active: Connection status (bool)
            - tx_kb: Transmitted traffic in KB (int)
            - rx_kb: Received traffic in KB (int)
            - tx_mb: Transmitted traffic in MB (float)
            - rx_mb: Received traffic in MB (float)
            - address_source: DHCP/STATIC (str)
            - lease_time: DHCP lease time in seconds (str)
            - rate_mbps: Connection speed in Mbps (int)
            - rssi: WiFi signal strength (int)
            - sta_rssi_dbm: WiFi signal in dBm (int)
            - phy_mode: WiFi protocol (str)
            - vendor_class: Device vendor identifier (str)
            - icon_type: Device type icon (str)
            - access_record: Last access timestamp (str)

    Example:
        >>> data = [{"Active": True, "MACAddress": "AA:BB:CC", ...}]
        >>> devices = process_host_devices(data)
        >>> print(devices[0]['connection_type'])
        'cable'
    """
    try:
        # Handle both list (API returns array directly) and dict with "Hosts" key
        if isinstance(host_data, list):
            all_hosts = host_data
        elif isinstance(host_data, dict):
            all_hosts = host_data.get("Hosts", [])
        else:
            all_hosts = []

        if not all_hosts:
            logger.warning("No hosts found in API response")
            return []

        active_hosts = _filter_active_hosts(all_hosts)
        processed_devices = _process_active_devices(active_hosts)

        logger.debug(
            f"Processed {len(processed_devices)} active devices "
            f"from {len(all_hosts)} total hosts"
        )
        return processed_devices

    except Exception as error:
        logger.error(f"Error processing host devices: {error}", exc_info=True)
        return []


def _filter_active_hosts(hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter only active hosts from the full host list.

    Args:
        hosts: List of all host dictionaries.

    Returns:
        List containing only hosts where Active is True.
    """
    return [host for host in hosts if host.get("Active", False)]


def _process_active_devices(active_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process each active host into standardized device format.

    Args:
        active_hosts: List of active host dictionaries.

    Returns:
        List of processed device dictionaries.
    """
    processed_devices = []

    for host in active_hosts:
        try:
            device_info = _extract_device_information(host)
            processed_devices.append(device_info)
        except Exception as error:
            mac_address = host.get("MACAddress", "unknown")
            logger.warning(
                f"Failed to process device {mac_address}: {error}", exc_info=True
            )
            continue

    return processed_devices


def _extract_device_information(host: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and normalize all device information from host data.

    Args:
        host: Raw host data dictionary from API.

    Returns:
        Normalized device information dictionary.
    """
    traffic_metrics = _extract_traffic_metrics(host)
    connection_metrics = _extract_connection_metrics(host)
    wifi_metrics = _extract_wifi_metrics(host)

    return {
        # Identification
        "mac": host.get("MACAddress", ""),
        "ip": host.get("IPAddress", ""),
        "ipv6": host.get("IPv6Address", ""),
        "hostname": host.get("HostName", DEFAULT_HOSTNAME),
        "actual_name": host.get("ActualName", ""),
        # Connection details
        "interface_type": host.get("InterfaceType", CONNECTION_TYPE_UNKNOWN),
        "layer2_interface": host.get("Layer2Interface", ""),
        "connection_type": _determine_connection_type(host),
        "active": host.get("Active", False),
        # Traffic metrics
        "tx_kb": traffic_metrics["tx_kb"],
        "rx_kb": traffic_metrics["rx_kb"],
        "tx_mb": traffic_metrics["tx_mb"],
        "rx_mb": traffic_metrics["rx_mb"],
        # IP configuration
        "address_source": host.get("AddressSource", ""),
        "lease_time": host.get("LeaseTime", DEFAULT_LEASE_TIME),
        # Connection metrics
        "rate_mbps": connection_metrics["rate_mbps"],
        # WiFi metrics
        "rssi": wifi_metrics["rssi"],
        "sta_rssi_dbm": wifi_metrics["sta_rssi_dbm"],
        "phy_mode": host.get("phyMode", ""),
        # Device metadata
        "vendor_class": host.get("VendorClassID", ""),
        "icon_type": host.get("IconType", ""),
        "access_record": host.get("AccessRecord", ""),
    }


def _extract_traffic_metrics(host: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and calculate traffic metrics from host data.

    Args:
        host: Host data dictionary.

    Returns:
        Dictionary with tx_kb, rx_kb, tx_mb, rx_mb keys.
    """
    transmitted_kb = _safe_int_conversion(host.get("TxKBytes", 0))
    received_kb = _safe_int_conversion(host.get("RxKBytes", 0))

    return {
        "tx_kb": transmitted_kb,
        "rx_kb": received_kb,
        "tx_mb": round(transmitted_kb / KILOBYTES_TO_MEGABYTES, 2),
        "rx_mb": round(received_kb / KILOBYTES_TO_MEGABYTES, 2),
    }


def _extract_connection_metrics(host: Dict[str, Any]) -> Dict[str, int]:
    """Extract connection speed metrics from host data.

    Args:
        host: Host data dictionary.

    Returns:
        Dictionary with rate_mbps key.
    """
    return {
        "rate_mbps": _safe_int_conversion(host.get("rate", 0)),
    }


def _extract_wifi_metrics(host: Dict[str, Any]) -> Dict[str, int]:
    """Extract WiFi signal strength metrics from host data.

    Args:
        host: Host data dictionary.

    Returns:
        Dictionary with rssi and sta_rssi_dbm keys.
    """
    return {
        "rssi": _safe_int_conversion(host.get("rssi", 0)),
        "sta_rssi_dbm": _safe_int_conversion(host.get("staRssi", 0)),
    }


def _safe_int_conversion(value: Any) -> int:
    """Safely convert value to integer, returning 0 on failure.

    Args:
        value: Value to convert.

    Returns:
        Integer value or 0 if conversion fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _determine_connection_type(host: Dict[str, Any]) -> str:
    """Determine connection type (cable/wifi) from interface type.

    Args:
        host: Host data dictionary.

    Returns:
        Connection type: 'cable', 'wifi', or 'unknown'.
    """
    interface_type = host.get("InterfaceType", "")

    if interface_type == INTERFACE_TYPE_LAN:
        return CONNECTION_TYPE_CABLE
    elif interface_type in [INTERFACE_TYPE_WIFI_2_4GHZ, INTERFACE_TYPE_WIFI_5GHZ]:
        return CONNECTION_TYPE_WIFI

    return CONNECTION_TYPE_UNKNOWN
