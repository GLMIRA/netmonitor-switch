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
            raise ValueError("INFLUXDB_TOKEN not found in environment variables")

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
            self.logger.error(f"Cannot write CPU data with error: {cpu_data['error']}")
            return False

        try:
            point = (
                Point("cpu_usage")
                .tag("switch_ip", cpu_data.get("switch_ip", "unknown"))
                .field("cpu_percent", cpu_data.get("cpu", 0))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(f"Wrote CPU data: {cpu_data.get('cpu')}%")
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
            self.logger.error(
                f"Cannot write system data with error: {system_data['error']}"
            )
            return False

        try:
            point = (
                Point("system_info")
                .tag("switch_ip", system_data.get("switch_ip", "unknown"))
                .tag("model", system_data.get("model", "unknown"))
                .field("uptime_seconds", system_data.get("uptime_seconds", 0))
                .field("temperature", system_data.get("temperature", 0))
                .field("firmware", system_data.get("firmware", "unknown"))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(
                f"Wrote system data: {system_data.get('temperature')}°C, "
                f"Uptime: {system_data.get('uptime_seconds')}s"
            )
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
            self.logger.error(
                f"Cannot write port data with error: {ports_data['error']}"
            )
            return False

        try:
            points = []
            for port in ports_data.get("ports", []):
                point = (
                    Point("port_traffic")
                    .tag("switch_ip", ports_data.get("switch_ip", "unknown"))
                    .tag("port", port.get("port", "unknown"))
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
                    .field("is_connected", port.get("link") == "up")
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
            for entry in mac_data.get("mac_table", []):
                point = (
                    Point("mac_addresses")
                    .tag("switch_ip", mac_data.get("switch_ip", "unknown"))
                    .tag("port", entry.get("port", "unknown"))
                    .tag("vlan", str(entry.get("vlan", "1")))
                    .tag("mac_address", entry.get("mac", "unknown"))
                    .field("type", entry.get("type", "unknown"))
                    .field("aging_time", entry.get("aging", 0))
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
        """Write switch logs to InfluxDB."""
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
                    .tag("module_name", self._get_module_name(log.get("module")))
                    .field("module_id", log.get("module"))
                    .field("severity_num", log.get("severity_num"))
                    .field("message", log.get("content", ""))
                    .field("source_ip", log.get("source_ip", ""))
                    .time(datetime.now(timezone.utc), WritePrecision.NS)
                )
                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
            self.logger.debug(f"Wrote {len(points)} log records")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write log data: {e}")
            return False

    def _get_module_name(self, module_id: int) -> str:
        """Convert TP-Link module ID to readable name.

        Args:
            module_id: Numeric module identifier from switch logs

        Returns:
            Human-readable module name
        """
        modules = {
            196: "WEB",
            170: "SYSTEM",
            174: "PORT",
            160: "VLAN",
            225: "STP",
            214: "MAC",
            215: "LOG",
            198: "CLI",
            182: "SNMP",
            166: "CONFIG",
            169: "AUTHENTICATION",
        }
        return modules.get(module_id, f"MODULE_{module_id}")

    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            self.client.close()
            self.logger.debug("InfluxDB connection closed")
