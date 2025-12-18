import os
import time

from dotenv import load_dotenv

from src.auth.auth_switch import switch_auth
from src.collectors.collectors_cpu import get_cpu_info
from src.collectors.collectors_logs import get_logs_switch
from src.collectors.collectors_mac import get_mac_address_info
from src.collectors.collectors_port import get_port_info
from src.collectors.collectors_system_time import get_sistem_time
from src.collectors.collector_status_port import get_status_port
from src.processors.cpu_processor import process_cpu_info
from src.processors.port_processors import (
    processor_port_trafic,
    processor_port_status,
    merge_port_data,
)
from src.processors.mac_processors import processor_mac_adress, count_macs_per_port
from src.processors.system_processor import processor_system_info
from src.processors.logs_processors import processor_logs
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

    # ========================================
    # CPU INFO
    # ========================================
    logger.info("=" * 50)
    logger.info("Testing CPU info...")
    cpu_raw = get_cpu_info(switch_ip, auth)
    logger.info(f"CPU RAW DATA: {cpu_raw}")

    cpu_processed = process_cpu_info(cpu_raw, switch_ip)
    logger.info(f"CPU PROCESSED DATA: {cpu_processed}")
    print(f"\n[CPU] Processed: {cpu_processed}\n")

    time.sleep(1)

    # ========================================
    # SYSTEM INFO
    # ========================================
    logger.info("=" * 50)
    logger.info("Testing system info...")
    system_raw = get_sistem_time(switch_ip, auth)
    logger.info(f"SYSTEM RAW DATA: {system_raw}")

    system_processed = processor_system_info(system_raw, switch_ip)
    logger.info(f"SYSTEM PROCESSED DATA: {system_processed}")
    print(f"\n[SYSTEM] Processed: {system_processed}\n")

    time.sleep(1)

    # ========================================
    # PORT STATUS + TRAFFIC (MERGED)
    # ========================================
    logger.info("=" * 50)
    logger.info("Testing port status...")
    port_status_raw = get_status_port(switch_ip, auth)
    logger.info(
        f"PORT STATUS RAW DATA (first 2): {port_status_raw.get('data', [])[:2]}"
    )

    port_status_processed = processor_port_status(port_status_raw)
    logger.info(
        f"PORT STATUS PROCESSED (first 2): {port_status_processed.get('ports', [])[:2]}"
    )

    time.sleep(1)

    logger.info("=" * 50)
    logger.info("Testing port traffic...")
    port_traffic_raw = get_port_info(switch_ip, auth)
    logger.info(
        f"PORT TRAFFIC RAW DATA (first 2): {port_traffic_raw.get('data', [])[:2]}"
    )

    port_traffic_processed = processor_port_trafic(port_traffic_raw)
    logger.info(
        f"PORT TRAFFIC PROCESSED (first 2): {port_traffic_processed.get('ports', [])[:2]}"
    )

    time.sleep(1)

    logger.info("=" * 50)
    logger.info("Merging port data...")
    merged_ports = merge_port_data(port_traffic_processed, port_status_processed)
    logger.info(f"MERGED PORT DATA (first 2): {merged_ports.get('ports', [])[:2]}")
    print(f"\n[PORTS] Merged (first 2): {merged_ports.get('ports', [])[:2]}\n")

    time.sleep(1)

    # ========================================
    # MAC TABLE
    # ========================================
    logger.info("=" * 50)
    logger.info("Testing MAC table...")
    mac_raw = get_mac_address_info(switch_ip, auth)
    logger.info(f"MAC RAW DATA (first 3): {mac_raw.get('data', [])[:3]}")

    mac_processed = processor_mac_adress(mac_raw)
    logger.info(
        f"MAC PROCESSED DATA (first 3): {mac_processed.get('mac_addresses', [])[:3]}"
    )

    mac_count = count_macs_per_port(mac_processed)
    logger.info(f"MAC COUNT PER PORT: {mac_count}")
    print(f"\n[MAC] Count per port: {mac_count}\n")

    time.sleep(1)

    # ========================================
    # LOGS
    # ========================================
    logger.info("=" * 50)
    logger.info("Testing switch logs...")
    logs_raw = get_logs_switch(switch_ip, auth)
    logger.info(
        f"LOGS RAW DATA (first 3): {logs_raw.get('data', [])[:3] if logs_raw.get('data') else 'No logs'}"
    )

    logs_processed = processor_logs(logs_raw, switch_ip)
    logger.info(f"LOGS PROCESSED (first 3): {logs_processed.get('logs', [])[:3]}")
    logger.info(f"LOGS SEVERITY COUNT: {logs_processed.get('severity_count', {})}")
    print(f"\n[LOGS] Severity count: {logs_processed.get('severity_count', {})}\n")

    time.sleep(1)

    # ========================================
    # SUMMARY
    # ========================================
    logger.info("=" * 50)
    logger.info("ALL TESTS COMPLETED SUCCESSFULLY!")
    logger.info(
        f"CPU Usage: {cpu_processed.get('cpu_usage_percent')}% ({cpu_processed.get('status')})"
    )
    logger.info(
        f"System: {system_processed.get('hostname')} - Temp: {system_processed.get('temperature')}°C ({system_processed.get('temp_status')}) - Uptime: {system_processed.get('uptime_days')} days"
    )
    logger.info(f"Total Ports Processed: {len(merged_ports.get('ports', []))}")
    logger.info(f"Total MAC Addresses: {len(mac_processed.get('mac_addresses', []))}")
    logger.info(f"Ports with devices: {len([p for p in mac_count.keys()])}")
    logger.info(f"Total Logs: {len(logs_processed.get('logs', []))}")


if __name__ == "__main__":
    main()
