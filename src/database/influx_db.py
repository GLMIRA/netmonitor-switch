import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

from src.utils.logger import get_logger


class InfluxDB:
    """InfluxDB client for writing switch monitoring data."""

    def __init__(self):
        """Initialize InfluxDB connection."""
        load_dotenv()
        self.logger = get_logger(__name__)

        # InfluxDB configuration
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "myorg")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "switch_monitoring")

        if not self.token:
            self.logger.error("INFLUXDB_TOKEN not set in environment variables")
            raise ValueError("Missing INFLUXDB_TOKEN")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.logger.info(f"Connected to InfluxDB at {self.url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def write_cpu_data(self, cpu_data: Dict) -> bool:
        """Write CPU data to InfluxDB.

        Args:
            cpu_data: Processed CPU data from process_cpu_info()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in cpu_data:
            self.logger.warning(
                f"Skipping CPU data write due to error: {cpu_data['error']}"
            )
            return False

        try:
            point = (
                Point("cpu_usage")
                .tag("switch_ip", cpu_data.get("switch_ip"))
                .tag("status", cpu_data.get("status"))
                .field("usage_percent", cpu_data.get("cpu_usage_percent"))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(
                f"Wrote CPU data for {cpu_data.get('switch_ip')}: {cpu_data.get('cpu_usage_percent')}%"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to write CPU data: {e}")
            return False

    def write_system_data(self, system_data: Dict) -> bool:
        """Write system information to InfluxDB.

        Args:
            system_data: Processed system data from processor_system_info()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in system_data:
            self.logger.warning(
                f"Skipping system data write due to error: {system_data['error']}"
            )
            return False

        try:
            point = (
                Point("system_info")
                .tag("switch_ip", system_data.get("switch_ip"))
                .tag("hostname", system_data.get("hostname"))
                .tag("temp_status", system_data.get("temp_status"))
                .tag("fan_status", system_data.get("fan_status"))
                .field("temperature", system_data.get("temperature"))
                .field("uptime_seconds", system_data.get("uptime_seconds"))
                .field("uptime_days", system_data.get("uptime_days"))
                .field("snmp_enabled", system_data.get("snmp_enabled"))
                .field("ssh_enabled", system_data.get("ssh_enabled"))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(f"Wrote system data for {system_data.get('hostname')}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write system data: {e}")
            return False

    def write_port_data(self, ports_data: Dict) -> bool:
        """Write port traffic and status data to InfluxDB.

        Args:
            ports_data: Merged port data from merge_port_data()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in ports_data:
            self.logger.warning(
                f"Skipping port data write due to error: {ports_data['error']}"
            )
            return False

        try:
            points = []
            for port in ports_data.get("ports", []):
                point = (
                    Point("port_traffic")
                    .tag("port", port.get("port"))
                    .tag("link", port.get("link", "unknown"))
                    .tag("state", port.get("state", "unknown"))
                    .field("packets_rx", port.get("packets_rx", 0))
                    .field("packets_tx", port.get("packets_tx", 0))
                    .field("bytes_rx", port.get("bytes_rx", 0))
                    .field("bytes_tx", port.get("bytes_tx", 0))
                    .field("bytes_rx_mb", port.get("bytes_rx_mb", 0.0))
                    .field("bytes_tx_mb", port.get("bytes_tx_mb", 0.0))
                    .field("total_packets", port.get("total_packets", 0))
                    .field("total_bytes", port.get("total_bytes", 0))
                    .field("is_connected", port.get("is_connected", False))
                    .time(datetime.now(timezone.utc), WritePrecision.NS)
                )
                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
            self.logger.debug(f"Wrote {len(points)} port records")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write port data: {e}")
            return False

    def write_mac_data(self, mac_data: Dict) -> bool:
        """Write MAC address table to InfluxDB.

        Args:
            mac_data: Processed MAC data from processor_mac_adress()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in mac_data:
            self.logger.warning(
                f"Skipping MAC data write due to error: {mac_data['error']}"
            )
            return False

        try:
            points = []
            for entry in mac_data.get("mac_addresses", []):
                point = (
                    Point("mac_table")
                    .tag("port", entry.get("port"))
                    .tag("mac", entry.get("mac"))
                    .tag("type", entry.get("type"))
                    .field("vlan", entry.get("vlan", 1))
                    .time(datetime.now(timezone.utc), WritePrecision.NS)
                )
                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
            self.logger.debug(f"Wrote {len(points)} MAC address records")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write MAC data: {e}")
            return False

    def write_log_data(self, logs_data: Dict) -> bool:
        """Write switch logs to InfluxDB.

        Args:
            logs_data: Processed logs from processor_logs()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in logs_data:
            self.logger.warning(
                f"Skipping logs write due to error: {logs_data['error']}"
            )
            return False

        try:
            points = []
            for log in logs_data.get("logs", []):
                point = (
                    Point("switch_logs")
                    .tag("switch_ip", log.get("switch_ip"))
                    .tag("severity", log.get("severity"))
                    .tag("source_ip", log.get("source_ip"))
                    .field("severity_num", log.get("severity_num"))
                    .field("module", log.get("module"))
                    .field("content", log.get("content"))
                    .time(datetime.now(timezone.utc), WritePrecision.NS)
                )
                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
            self.logger.debug(f"Wrote {len(points)} log records")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write log data: {e}")
            return False

    def close(self):
        """Close InfluxDB connection."""
        try:
            self.client.close()
            self.logger.info("Closed InfluxDB connection")
        except Exception as e:
            self.logger.error(f"Error closing InfluxDB connection: {e}")
