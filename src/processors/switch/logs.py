import re
from src.utils.logger import get_logger


def parse_severity(severity: int) -> str:
    """Convert severity number to text.

    Args:
        severity: Severity level (0-7)

    Returns:
        str: Severity name
    """
    severity_map = {
        0: "emergency",
        1: "alert",
        2: "critical",
        3: "error",
        4: "warning",
        5: "notice",
        6: "informational",
        7: "debug",
    }
    return severity_map.get(severity, "unknown")


def extract_ip_from_content(content: str) -> str:
    """Extract IP address from log content.

    Args:
        content: Log message like 'Login by admin (192.168.137.201)'

    Returns:
        str: IP address or 'unknown'
    """
    match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", content)
    return match.group(1) if match else "unknown"


def processor_logs(raw_data: dict, switch_ip: str) -> dict:
    """Process switch logs.

    Args:
        raw_data: Raw response from get_logs_switch()
        switch_ip: IP address of the switch

    Returns:
        dict: Processed log entries
    """
    logger = get_logger(__name__)

    if "error" in raw_data:
        logger.error(f"Error retrieving logs from {switch_ip}: {raw_data['error']}")
        return {"error": raw_data["error"]}

    if not raw_data.get("success"):
        logger.warning(f"API returned success=False for logs from {switch_ip}")
        return {"error": "API request failed"}

    # Handle case where no logs are returned
    if "data" not in raw_data or not isinstance(raw_data.get("data"), list):
        logger.info(f"No logs available from {switch_ip}")
        return {"logs": []}

    try:
        logs_list = raw_data["data"]
        processed_logs = []
        severity_count = {}

        for log_entry in logs_list:
            try:
                severity_num = log_entry.get("severity", 6)
                severity_text = parse_severity(severity_num)

                # Count by severity
                severity_count[severity_text] = severity_count.get(severity_text, 0) + 1

                # Extract source IP if present
                content = log_entry.get("content", "").strip()
                source_ip = extract_ip_from_content(content)

                processed_log = {
                    "switch_ip": switch_ip,
                    "timestamp": log_entry.get("time", ""),
                    "module": log_entry.get("module", 0),
                    "severity": severity_text,
                    "severity_num": severity_num,
                    "content": content,
                    "source_ip": source_ip,
                }

                processed_logs.append(processed_log)

            except (KeyError, ValueError) as e:
                logger.warning(
                    f"Error processing individual log entry from {switch_ip}: {e}"
                )
                continue

        # Log summary
        logger.info(f"Processed {len(processed_logs)} logs from {switch_ip}")
        logger.debug(f"Logs by severity: {severity_count}")

        return {"logs": processed_logs, "severity_count": severity_count}

    except TypeError as e:
        logger.error(f"Malformed log data from {switch_ip}: {e}")
        return {"error": f"Malformed data: {e}"}
    except Exception as e:
        logger.error(
            f"Unexpected error processing logs from {switch_ip}: {e}", exc_info=True
        )
        return {"error": str(e)}
