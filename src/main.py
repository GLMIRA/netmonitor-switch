import os
import time

from dotenv import load_dotenv

from src.auth.auth_switch import switch_auth
from src.get_info.cpu_info import get_cpu_info
from src.get_info.logs_switch import get_logs_switch
from src.get_info.mac_adress import get_mac_address_info
from src.get_info.port_util import get_port_info
from src.get_info.system_time import get_sistem_time
from src.get_info.status_port import get_status_port
from src.utils.logger import setup_logging, get_logger


def main():
    """Main function to test all switch data retrieval functions."""

    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)

    # Load environment variables
    load_dotenv()
    switch_ip = os.getenv("SWITCH_IP")
    username = os.getenv("SWITCH_USER")
    password = os.getenv("SWITCH_PASSWORD")

    # Validate environment variables
    if not all([switch_ip, username, password]):
        logger.error(
            "Missing required environment variables (SWITCH_IP, SWITCH_USER, SWITCH_PASSWORD)"
        )
        return

    logger.info(f"Starting data retrieval for switch at {switch_ip}")

    # Authenticate
    auth = switch_auth(switch_ip, username, password, "write")
    if "error" in auth:
        logger.error(f"Authentication failed: {auth['error']}")
        return

    logger.info("Authentication successful!")

    # Test all functions
    logger.info("Testing CPU info...")
    cpu_data = get_cpu_info(switch_ip, auth)
    print(f"CPU Info: {cpu_data}")

    time.sleep(1)

    logger.info("Testing system time...")
    time_data = get_sistem_time(switch_ip, auth)
    print(f"System Time: {time_data}")

    time.sleep(5)

    logger.info("Testing port status...")
    port_status = get_status_port(switch_ip, auth)
    print(f"Port Status: {port_status}")

    time.sleep(1)

    logger.info("Testing port traffic...")
    port_traffic = get_port_info(switch_ip, auth)
    print(f"Port Traffic: {port_traffic}")

    time.sleep(1)

    logger.info("Testing MAC table...")
    mac_table = get_mac_address_info(switch_ip, auth)
    print(f"MAC Table: {mac_table}")

    time.sleep(1)

    logger.info("Testing switch logs...")
    logs = get_logs_switch(switch_ip, auth)
    print(f"Switch Logs: {logs}")

    time.sleep(1)

    logger.info("All tests completed successfully!")


if __name__ == "__main__":
    main()
