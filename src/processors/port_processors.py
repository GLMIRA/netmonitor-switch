from src.utils.logger import get_logger


def clean_numeric(value: str) -> int:
    """Cleans and converts a numeric string with commas to an integer.

    Args:
        value (str): The numeric string to clean.

    Returns:
        int: The cleaned integer value.
    """
    try:
        return int(value.replace(",", ""))
    except (ValueError, AttributeError):
        return 0


def processor_port_trafic(raw_data: dict) -> dict:
    """
    Recive port information trafic por and format that
    Args:
        raw_data (dict): Raw port information dictionary
    """

    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(f"Error retrieving port trafic info: {raw_data['error']}")
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning("API returned success=False for port trafic info")
        return {"error": "API request failed"}

    if "data" not in raw_data:
        logger.warning("Missing 'data' key in port trafic response")
        return {"error": "Incomplete response"}

    try:
        ports_list = raw_data["data"]

        if not isinstance(ports_list, list):
            logger.warning("Port trafic data is not in expected list format")
            return {"error": "Invalid data format"}

        processed_ports = []

        for port_data in ports_list:
            logger.debug(f"Raw port data: {port_data}")
            port_number = port_data.get("port")

            packets_rx = clean_numeric(port_data.get("packetRx"))
            bytes_rx = clean_numeric(port_data.get("octetsRx"))
            packets_tx = clean_numeric(port_data.get("packetTx"))
            bytes_tx = clean_numeric(port_data.get("octetsTx"))

            total_packets = packets_rx + packets_tx
            total_bytes = bytes_rx + bytes_tx

            bytes_rx_mb = round(bytes_rx / (1024 * 1024), 2)
            bytes_tx_mb = round(bytes_tx / (1024 * 1024), 2)

            logger.debug(
                f"Processing port {port_number} with rxPkts: {packets_rx}, txPkts: {packets_tx}, rxBytes: {bytes_rx}, txBytes: {bytes_tx}"
            )

            processed_port = {
                "port": port_number,
                "packets_rx": packets_rx,
                "packets_tx": packets_tx,
                "bytes_rx": bytes_rx,
                "bytes_tx": bytes_tx,
                "bytes_rx_mb": bytes_rx_mb,
                "bytes_tx_mb": bytes_tx_mb,
                "total_packets": total_packets,
                "total_bytes": total_bytes,
            }

            logger.info(f"Processed port trafic info: {processed_port}")
            processed_ports.append(processed_port)

        return {"ports": processed_ports}
    except (KeyError, TypeError) as e:
        logger.error(f"Malformed port trafic data: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(
            f"Unexpected error processing port trafic info: {e}", exc_info=True
        )
        return {"error": str(e)}


def processor_port_status(raw_data: dict) -> dict:
    """
    Recive port status information and format that
    Args:
        raw_data (dict): Raw port status information dictionary
    """

    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(f"Error retrieving port status info: {raw_data['error']}")
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning("API returned success=False for port status info")
        return {"error": "API request failed"}

    if "data" not in raw_data:
        logger.warning("Missing 'data' key in port status response")
        return {"error": "Incomplete response"}

    try:
        ports_list = raw_data["data"]

        if not isinstance(ports_list, list):
            logger.warning("Port status data is not in expected list format")
            return {"error": "Invalid data format"}

        processed_ports = []

        for port_data in ports_list:
            port_number = port_data.get("port")

            link_raw = port_data.get("link", "Unknown")
            link = link_raw.lower() if isinstance(link_raw, str) else "unknown"

            state_raw = port_data.get("state", "Unknown")
            state = str(state_raw).lower() if state_raw != "Unknown" else "unknown"

            speed_raw = port_data.get("speed", "Unknown")
            speed = (
                speed_raw.split()[0].lower()
                if isinstance(speed_raw, str) and speed_raw != "Unknown"
                else "unknown"
            )

            is_connected = link == "up"

            processed_port = {
                "port": port_number,
                "link": link,
                "state": state,
                "speed": speed,
                "is_connected": is_connected,
            }
            logger.info(f"Processed port status info: {processed_port}")
            processed_ports.append(processed_port)
        return {"ports": processed_ports}
    except (KeyError, TypeError) as e:
        logger.error(f"Malformed port status data: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error processing port status: {e}", exc_info=True)
        return {"error": str(e)}


def merge_port_data(trafic_data: dict, status_data: dict) -> dict:
    """
    Merge port trafic and status information into a single structure
    Args:
        trafic_data (dict): Processed port trafic information
        status_data (dict): Processed port status information
    """

    logger = get_logger(__name__)

    if "error" in trafic_data:
        logger.error(f"Error in trafic data: {trafic_data['error']}")
        return {"error": trafic_data["error"]}

    if "error" in status_data:
        logger.error(f"Error in status data: {status_data['error']}")
        return {"error": status_data["error"]}

    try:
        merged_ports = []
        status_dict = {port["port"]: port for port in status_data.get("ports", [])}

        for trafic_port in trafic_data.get("ports", []):
            port_number = trafic_port["port"]
            status_port = status_dict.get(port_number, {})

            merged_port = {
                **trafic_port,
                **status_port,
            }
            logger.info(f"Merged port data: {merged_port}")
            merged_ports.append(merged_port)

        return {"ports": merged_ports}
    except Exception as e:
        logger.error(f"Unexpected error merging port data: {e}", exc_info=True)
        return {"error": str(e)}
