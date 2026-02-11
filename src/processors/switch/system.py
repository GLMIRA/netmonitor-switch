import re
from src.utils.logger import get_logger


def parse_uptime(uptime_str: str) -> int:
    """Convert uptime string to seconds.

    Args:
        uptime_str: String like '7 day - 12 hour - 17 min - 49 sec'

    Returns:
        int: Total uptime in seconds
    """
    try:
        days = (
            int(re.search(r"(\d+)\s*day", uptime_str).group(1))
            if "day" in uptime_str
            else 0
        )
        hours = (
            int(re.search(r"(\d+)\s*hour", uptime_str).group(1))
            if "hour" in uptime_str
            else 0
        )
        minutes = (
            int(re.search(r"(\d+)\s*min", uptime_str).group(1))
            if "min" in uptime_str
            else 0
        )
        seconds = (
            int(re.search(r"(\d+)\s*sec", uptime_str).group(1))
            if "sec" in uptime_str
            else 0
        )

        return days * 86400 + hours * 3600 + minutes * 60 + seconds
    except (AttributeError, ValueError) as e:
        logger = get_logger(__name__)
        logger.error(f"Error parsing uptime '{uptime_str}': {e}")
        return 0


def processor_system_info(raw_data: dict, switch_ip: str) -> dict:
    """Process system information from switch.

    Args:
        raw_data: Raw response from get_sistem_time()
        switch_ip: IP address of the switch

    Returns:
        dict: Processed system metrics
    """
    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(
            f"Error retrieving system info from {switch_ip}: {raw_data['error']}"
        )
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning(f"API returned success=False for system info from {switch_ip}")
        return {"error": "API request failed"}

    if "data" not in raw_data:
        logger.warning(f"Missing 'data' key in system info response from {switch_ip}")
        return {"error": "Incomplete response"}

    try:
        data = raw_data["data"]

        # Parse uptime
        uptime_str = data.get("run_time", "0 sec")
        uptime_seconds = parse_uptime(uptime_str)
        uptime_days = round(uptime_seconds / 86400, 2)

        # Temperature status
        temp = data.get("temperature", 0)
        if temp > 90:
            temp_status = "critical"
        elif temp > 80:
            temp_status = "warning"
        else:
            temp_status = "normal"

        # Fan status
        fan_sta = data.get("fan_sta", 0)
        fan_status = "ok" if fan_sta == 1 else "fail"

        # Normalize MAC address
        mac_raw = data.get("mac_address", "Unknown")
        mac_normalized = (
            mac_raw.replace("-", ":").lower() if mac_raw != "Unknown" else "unknown"
        )

        # SNMP and SSH status
        snmp_enabled = data.get("snmp_sta") == 1
        ssh_enabled = data.get("ssh_sta") == 1

        processed_data = {
            "switch_ip": switch_ip,
            "hostname": data.get("dev_name", "Unknown"),
            "location": data.get("dev_loc", "Unknown"),
            "mac_address": mac_normalized,
            "mac_original": mac_raw,
            "firmware_version": data.get("fw_version", "Unknown"),
            "hardware_version": data.get("hw_version", "Unknown"),
            "serial_number": data.get("se_number", "Unknown"),
            "uptime_seconds": uptime_seconds,
            "uptime_days": uptime_days,
            "temperature": temp,
            "temp_status": temp_status,
            "fan_status": fan_status,
            "snmp_enabled": snmp_enabled,
            "ssh_enabled": ssh_enabled,
        }

        logger.info(
            f"Processed system info from {switch_ip}: {processed_data['hostname']} (temp: {temp}°C, uptime: {uptime_days} days)"
        )
        return processed_data

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Malformed system info data from {switch_ip}: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(
            f"Unexpected error processing system info from {switch_ip}: {e}",
            exc_info=True,
        )
        return {"error": str(e)}
