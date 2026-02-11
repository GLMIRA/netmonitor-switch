import os
from datetime import datetime, timezone
from typing import Dict, List

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

from src.utils.logger import get_logger


class InfluxDBSwitch:
    """InfluxDB client for writing switch monitoring data."""

    def __init__(self):
        """Initialize InfluxDB connection."""
        load_dotenv()
        self.logger = get_logger(__name__)

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


class InfluxDBRouter:
    """InfluxDB client for writing router monitoring data."""

    def __init__(self):
        """Initialize InfluxDB connection."""
        load_dotenv()
        self.logger = get_logger(__name__)

        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "myorg")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "router_monitoring")

        if not self.token:
            raise ValueError("INFLUXDB_TOKEN not found in environment variables")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.logger.info(
                f"Connected to InfluxDB at {self.url} for router monitoring"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def write_host_summary(self, host_summary: Dict) -> bool:
        """Write aggregated host metrics to InfluxDB.

        Args:
            host_summary: Processed host summary data from process_host_summary()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in host_summary:
            self.logger.error(
                f"Cannot write host summary with error: {host_summary['error']}"
            )
            return False

        try:
            point = (
                Point("host_summary")
                .tag("router_ip", host_summary.get("router_ip", "unknown"))
                .field("total_devices", host_summary.get("total_devices", 0))
                .field("devices_online", host_summary.get("devices_online", 0))
                .field("devices_offline", host_summary.get("devices_offline", 0))
                .field("devices_lan", host_summary.get("devices_lan", 0))
                .field(
                    "devices_wifi_2_4ghz", host_summary.get("devices_wifi_2_4ghz", 0)
                )
                .field("devices_wifi_5ghz", host_summary.get("devices_wifi_5ghz", 0))
                .field("devices_dhcp", host_summary.get("devices_dhcp", 0))
                .field("devices_static", host_summary.get("devices_static", 0))
                .field(
                    "total_traffic_tx_kb", host_summary.get("total_traffic_tx_kb", 0)
                )
                .field(
                    "total_traffic_rx_kb", host_summary.get("total_traffic_rx_kb", 0)
                )
                .field(
                    "total_traffic_tx_mb", host_summary.get("total_traffic_tx_mb", 0.0)
                )
                .field(
                    "total_traffic_rx_mb", host_summary.get("total_traffic_rx_mb", 0.0)
                )
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(
                f"Wrote host summary: {host_summary.get('devices_online')} online, "
                f"{host_summary.get('total_traffic_rx_mb')} MB RX"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to write host summary: {e}")
            return False

    def write_host_devices(self, devices_data: List[Dict]) -> bool:
        """Write individual device information to InfluxDB.

        Args:
            devices_data: List of processed device data from process_host_devices()

        Returns:
            bool: True if successful, False otherwise
        """
        if not devices_data:
            self.logger.warning("No device data to write")
            return False

        try:
            points = []
            for device in devices_data:
                point = (
                    Point("host_devices")
                    .tag("router_ip", device.get("router_ip", "unknown"))
                    .tag("mac", device.get("mac", "unknown"))
                    .tag("ip", device.get("ip", "unknown"))
                    .tag("interface_type", device.get("interface_type", "unknown"))
                    .tag("connection_type", device.get("connection_type", "unknown"))
                    .field("hostname", device.get("hostname", "Unknown"))
                    .field("actual_name", device.get("actual_name", ""))
                    .field("ipv6", device.get("ipv6", ""))
                    .field("layer2_interface", device.get("layer2_interface", ""))
                    .field("active", device.get("active", False))
                    .field("tx_kb", device.get("tx_kb", 0))
                    .field("rx_kb", device.get("rx_kb", 0))
                    .field("tx_mb", device.get("tx_mb", 0.0))
                    .field("rx_mb", device.get("rx_mb", 0.0))
                    .field("address_source", device.get("address_source", ""))
                    .field("lease_time", device.get("lease_time", "0"))
                    .field("rate_mbps", device.get("rate_mbps", 0))
                    .field("rssi", device.get("rssi", 0))
                    .field("sta_rssi_dbm", device.get("sta_rssi_dbm", 0))
                    .field("phy_mode", device.get("phy_mode", ""))
                    .field("vendor_class", device.get("vendor_class", ""))
                    .field("icon_type", device.get("icon_type", ""))
                    .time(datetime.now(timezone.utc), WritePrecision.NS)
                )
                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
            self.logger.debug(f"Wrote {len(points)} device records")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write host devices: {e}")
            return False

    def write_wan_status(self, wan_status: Dict) -> bool:
        """Write WAN connection status to InfluxDB.

        Args:
            wan_status: Processed WAN status data from process_wan_status()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in wan_status:
            self.logger.error(
                f"Cannot write WAN status with error: {wan_status['error']}"
            )
            return False

        try:
            point = (
                Point("wan_status")
                .tag("router_ip", wan_status.get("router_ip", "unknown"))
                .tag("interface_name", wan_status.get("interface_name", "unknown"))
                .field("connection_status", wan_status.get("connection_status", ""))
                .field(
                    "ipv6_connection_status",
                    wan_status.get("ipv6_connection_status", ""),
                )
                .field("access_status", wan_status.get("access_status", ""))
                .field("is_connected", wan_status.get("is_connected", False))
                .field("interface_enabled", wan_status.get("interface_enabled", False))
                .field("interface_alias", wan_status.get("interface_alias", ""))
                .field("ipv4_address", wan_status.get("ipv4_address", ""))
                .field("ipv4_gateway", wan_status.get("ipv4_gateway", ""))
                .field("ipv4_mask", wan_status.get("ipv4_mask", ""))
                .field("ipv6_address", wan_status.get("ipv6_address", ""))
                .field("ipv6_address_full", wan_status.get("ipv6_address_full", ""))
                .field("ipv6_prefix_length", wan_status.get("ipv6_prefix_length", 0))
                .field("ipv6_gateway", wan_status.get("ipv6_gateway", ""))
                .field("ipv4_dns_servers", wan_status.get("ipv4_dns_servers", ""))
                .field("ipv6_dns_servers", wan_status.get("ipv6_dns_servers", ""))
                .field("pppoe_username", wan_status.get("pppoe_username", ""))
                .field("pppoe_ac_name", wan_status.get("pppoe_ac_name", ""))
                .field("connection_type", wan_status.get("connection_type", ""))
                .field("wan_type", wan_status.get("wan_type", ""))
                .field("ipv4_enabled", wan_status.get("ipv4_enabled", False))
                .field("ipv6_enabled", wan_status.get("ipv6_enabled", False))
                .field("nat_type", wan_status.get("nat_type", 0))
                .field("mtu", wan_status.get("mtu", 0))
                .field("mru", wan_status.get("mru", 0))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(
                f"Wrote WAN status: {wan_status.get('connection_status')}, "
                f"IPv4: {wan_status.get('ipv4_address')}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to write WAN status: {e}")
            return False

    def write_wan_bandwidth(self, wan_bandwidth: Dict) -> bool:
        """Write WAN bandwidth metrics to InfluxDB.

        Args:
            wan_bandwidth: Processed WAN bandwidth data from process_wan_bandwidth()

        Returns:
            bool: True if successful, False otherwise
        """
        if "error" in wan_bandwidth:
            self.logger.error(
                f"Cannot write WAN bandwidth with error: {wan_bandwidth['error']}"
            )
            return False

        try:
            point = (
                Point("wan_bandwidth")
                .tag("router_ip", wan_bandwidth.get("router_ip", "unknown"))
                .field(
                    "upload_current_kbps", wan_bandwidth.get("upload_current_kbps", 0)
                )
                .field(
                    "download_current_kbps",
                    wan_bandwidth.get("download_current_kbps", 0),
                )
                .field(
                    "upload_current_mbps", wan_bandwidth.get("upload_current_mbps", 0.0)
                )
                .field(
                    "download_current_mbps",
                    wan_bandwidth.get("download_current_mbps", 0.0),
                )
                .field("upload_max_kbps", wan_bandwidth.get("upload_max_kbps", 0))
                .field("download_max_kbps", wan_bandwidth.get("download_max_kbps", 0))
                .field("upload_max_mbps", wan_bandwidth.get("upload_max_mbps", 0.0))
                .field("download_max_mbps", wan_bandwidth.get("download_max_mbps", 0.0))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(
                f"Wrote WAN bandwidth: ↑{wan_bandwidth.get('upload_current_mbps')} Mbps, "
                f"↓{wan_bandwidth.get('download_current_mbps')} Mbps"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to write WAN bandwidth: {e}")
            return False

    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            self.client.close()
            self.logger.debug("InfluxDB connection closed")
