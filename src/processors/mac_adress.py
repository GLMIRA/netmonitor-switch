from src.utils.logger import get_logger


def normalize_mac(mac: str) -> str:
    """Normalize MAC address format.

    Args:
        mac: MAC address like '00-1A-3F-87-0F-7A'

    Returns:
        str: Normalized MAC like '00:1a:3f:87:0f:7a'
    """
    return mac.replace("-", ":").lower()


def processor_mac_adress(raw_data: dict) -> dict:
    """Recive data brut normlize it and return useful information.
    Args:
        data: Raw MAC Address information dictionary
    Returns:
        dict: Processed MAC address information
    """
    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(f"Error retrieving MAC address info: {raw_data['error']}")
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning("API returned success=False for MAC address info")
        return {"error": "API request failed"}

    if "data" not in raw_data:
        logger.warning("Missing 'data' key in MAC address response")
        return {"error": "Incomplete response"}

    try:
        mac_table = raw_data["data"]

        if not isinstance(mac_table, list):
            logger.warning("MAC address data is not in expected list format")
            return {"error": "Invalid data format"}

        processed_macs = []

        for entry in mac_table:
            vlan = entry.get("vlanId", 1)
            mac_raw = entry.get("mac", "Unknown")
            mac_normalized = normalize_mac(mac_raw)
            port = entry.get("port", "Unknown")
            entry_type = "static" if entry.get("type") == 2 else "dynamic"

            processed_entry = {
                "vlan": vlan,
                "mac": mac_normalized,
                "mac_original": mac_raw,
                "port": port,
                "type": entry_type,
            }

            logger.debug(f"Processed MAC entry: {processed_entry}")
            processed_macs.append(processed_entry)

        logger.info(f"Processed {len(processed_macs)} MAC addresses")
        return {"mac_addresses": processed_macs}

    except (KeyError, TypeError) as e:
        logger.error(f"Malformed MAC address data: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error processing MAC addresses: {e}", exc_info=True)
        return {"error": str(e)}


def count_macs_per_port(processed_data: dict) -> dict:
    """Count MAC addresses per port.

    Args:
        processed_data: Result from processor_mac_adress()

    Returns:
        dict: MAC count indexed by port {"1/0/13": 2, "1/0/5": 1}
    """
    logger = get_logger(__name__)

    if "error" in processed_data:
        logger.warning("Cannot count MACs due to error in processed data")
        return {}

    mac_count = {}
    for entry in processed_data.get("mac_addresses", []):
        port = entry["port"]
        mac_count[port] = mac_count.get(port, 0) + 1

    logger.info(f"MAC count per port: {mac_count}")
    logger.debug(f"Detailed count: {mac_count}")

    return mac_count
