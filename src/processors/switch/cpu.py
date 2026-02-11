from src.utils.logger import get_logger


def process_cpu_info(raw_data: dict, switch_ip: str) -> dict:
    """Recive data brut normlize it and return useful information.
    Args:
        data: Raw CPU information dictionary

    Returns:
        dict: Processed CPU information with useful metrics
    """

    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(
            f"Error retrieving CPU info from switch at {switch_ip}: {raw_data['error']}"
        )
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning(f"API returned success=False for {switch_ip}")
        return {"error": "API request failed"}

    if "data" not in raw_data:
        logger.warning(f"Missing 'data' key in response from {switch_ip}")
        return {"error": "Incomplete response"}

    try:
        cpu_usage = raw_data["data"]["cpu"][0]

        if not (0 <= cpu_usage <= 100):
            logger.warning(f"Invalid CPU value {cpu_usage}% from {switch_ip}")
            return {"error": f"Invalid CPU value: {cpu_usage}"}

        if cpu_usage >= 90:
            logger.warning(f"Critical CPU usage on switch at {switch_ip}: {cpu_usage}%")
            status = "critical"
        elif cpu_usage >= 70:
            logger.warning(f"High CPU usage on switch at {switch_ip}: {cpu_usage}%")
            status = "warning"
        else:
            status = "normal"

        processed_data = {
            "switch_ip": switch_ip,
            "cpu_usage_percent": cpu_usage,
            "status": status,
        }
        logger.info(f"Processed CPU info from switch at {switch_ip}: {processed_data}")
        return processed_data
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Malformed CPU info data from switch at {switch_ip}: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(
            f"Unexpected error processing CPU info from switch at {switch_ip}: {e}",
            exc_info=True,
        )
        return {"error": str(e)}
