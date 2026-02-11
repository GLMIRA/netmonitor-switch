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
        self.bucket = os.getenv("INFLUXDB_BUCKET_SWITCH", "switch_monitoring")

        if not self.token:
            raise ValueError("INFLUXDB_TOKEN not found in environment variables")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self._ensure_bucket()
            self.logger.info(
                f"Connected to InfluxDB at {self.url} (bucket: {self.bucket})"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            buckets_api = self.client.buckets_api()
            if not buckets_api.find_bucket_by_name(self.bucket):
                buckets_api.create_bucket(bucket_name=self.bucket, org=self.org)
                self.logger.info(f"Created bucket: {self.bucket}")
        except Exception as e:
            self.logger.warning(f"Could not verify/create bucket '{self.bucket}': {e}")

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
                .tag("switch_ip", cpu_data["switch_ip"])
                .field("cpu_percent", cpu_data["cpu_usage_percent"])
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.debug(f"Wrote CPU data: {cpu_data.get('cpu_usage_percent')}%")
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
                .tag("switch_ip", system_data.get("switch_ip"))
                .tag("model", system_data.get("hardware_version"))
                .field("uptime_seconds", system_data.get("uptime_seconds"))
                .field("temperature", system_data.get("temperature"))
                .field("firmware", system_data.get("firmware_version"))
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
            for port in ports_data["ports"]:
                point = (
                    Point("port_traffic")
                    .tag("switch_ip", ports_data["switch_ip"])
                    .tag("port", port["port"])
                    .tag("link", port["link"])
                    .tag("state", port["state"])
                    .field("packets_rx", port["packets_rx"])
                    .field("packets_tx", port["packets_tx"])
                    .field("bytes_rx", port["bytes_rx"])
                    .field("bytes_tx", port["bytes_tx"])
                    .field("bytes_rx_mb", port["bytes_rx_mb"])
                    .field("bytes_tx_mb", port["bytes_tx_mb"])
                    .field("total_packets", port["total_packets"])
                    .field("total_bytes", port["total_bytes"])
                    .field("is_connected", port["link"] == "up")
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
            for entry in mac_data["mac_addresses"]:
                point = (
                    Point("mac_addresses")
                    .tag("switch_ip", mac_data["switch_ip"])
                    .tag("port", entry["port"])
                    .tag("vlan", str(entry["vlan"]))
                    .tag("mac_address", entry["mac"])
                    .field("type", entry["type"])
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
            for log in logs_data["logs"]:
                point = (
                    Point("switch_logs")
                    .tag("switch_ip", log["switch_ip"])
                    .tag("severity", log["severity"])
                    .tag("module_name", self._get_module_name(log["module"]))
                    .field("module_id", log["module"])
                    .field("severity_num", log["severity_num"])
                    .field("message", log.get("content"))
                    .field("source_ip", log.get("source_ip"))
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
        self.bucket = os.getenv("INFLUXDB_BUCKET_ROUTER", "router_monitoring")

        if not self.token:
            raise ValueError("INFLUXDB_TOKEN not found in environment variables")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self._ensure_bucket()
            self.logger.info(
                f"Connected to InfluxDB at {self.url} (bucket: {self.bucket})"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            buckets_api = self.client.buckets_api()
            if not buckets_api.find_bucket_by_name(self.bucket):
                buckets_api.create_bucket(bucket_name=self.bucket, org=self.org)
                self.logger.info(f"Created bucket: {self.bucket}")
        except Exception as e:
            self.logger.warning(f"Could not verify/create bucket '{self.bucket}': {e}")

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
                .tag("router_ip", host_summary["router_ip"])
                .field("total_devices", host_summary["total_devices"])
                .field("devices_online", host_summary["devices_online"])
                .field("devices_offline", host_summary["devices_offline"])
                .field("devices_lan", host_summary["devices_lan"])
                .field("devices_wifi_2_4ghz", host_summary["devices_wifi_2_4ghz"])
                .field("devices_wifi_5ghz", host_summary["devices_wifi_5ghz"])
                .field("devices_dhcp", host_summary["devices_dhcp"])
                .field("devices_static", host_summary["devices_static"])
                .field("total_traffic_tx_kb", host_summary["total_traffic_tx_kb"])
                .field("total_traffic_rx_kb", host_summary["total_traffic_rx_kb"])
                .field("total_traffic_tx_mb", host_summary["total_traffic_tx_mb"])
                .field("total_traffic_rx_mb", host_summary["total_traffic_rx_mb"])
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
                    .tag("router_ip", device["router_ip"])
                    .tag("mac", device["mac"])
                    .tag("ip", device["ip"])
                    .tag("interface_type", device["interface_type"])
                    .tag("connection_type", device["connection_type"])
                    .field("hostname", device["hostname"])
                    .field("actual_name", device.get("actual_name"))
                    .field("ipv6", device.get("ipv6"))
                    .field("layer2_interface", device.get("layer2_interface"))
                    .field("active", device["active"])
                    .field("tx_kb", device["tx_kb"])
                    .field("rx_kb", device["rx_kb"])
                    .field("tx_mb", device["tx_mb"])
                    .field("rx_mb", device["rx_mb"])
                    .field("address_source", device.get("address_source"))
                    .field("lease_time", device.get("lease_time"))
                    .field("rate_mbps", device.get("rate_mbps"))
                    .field("rssi", device.get("rssi"))
                    .field("sta_rssi_dbm", device.get("sta_rssi_dbm"))
                    .field("phy_mode", device.get("phy_mode"))
                    .field("vendor_class", device.get("vendor_class"))
                    .field("icon_type", device.get("icon_type"))
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
                .tag("router_ip", wan_status["router_ip"])
                .tag("interface_name", wan_status["interface_name"])
                .field("connection_status", wan_status.get("connection_status"))
                .field(
                    "ipv6_connection_status", wan_status.get("ipv6_connection_status")
                )
                .field("access_status", wan_status.get("access_status"))
                .field("is_connected", wan_status["is_connected"])
                .field("interface_enabled", wan_status.get("interface_enabled"))
                .field("interface_alias", wan_status.get("interface_alias"))
                .field("ipv4_address", wan_status.get("ipv4_address"))
                .field("ipv4_gateway", wan_status.get("ipv4_gateway"))
                .field("ipv4_mask", wan_status.get("ipv4_mask"))
                .field("ipv6_address", wan_status.get("ipv6_address"))
                .field("ipv6_address_full", wan_status.get("ipv6_address_full"))
                .field("ipv6_prefix_length", wan_status.get("ipv6_prefix_length"))
                .field("ipv6_gateway", wan_status.get("ipv6_gateway"))
                .field("ipv4_dns_servers", wan_status.get("ipv4_dns_servers"))
                .field("ipv6_dns_servers", wan_status.get("ipv6_dns_servers"))
                .field("pppoe_username", wan_status.get("pppoe_username"))
                .field("pppoe_ac_name", wan_status.get("pppoe_ac_name"))
                .field("connection_type", wan_status.get("connection_type"))
                .field("wan_type", wan_status.get("wan_type"))
                .field("ipv4_enabled", wan_status.get("ipv4_enabled"))
                .field("ipv6_enabled", wan_status.get("ipv6_enabled"))
                .field("nat_type", wan_status.get("nat_type"))
                .field("mtu", wan_status.get("mtu"))
                .field("mru", wan_status.get("mru"))
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
                .tag("router_ip", wan_bandwidth["router_ip"])
                .field("upload_current_kbps", wan_bandwidth["upload_current_kbps"])
                .field("download_current_kbps", wan_bandwidth["download_current_kbps"])
                .field("upload_current_mbps", wan_bandwidth["upload_current_mbps"])
                .field("download_current_mbps", wan_bandwidth["download_current_mbps"])
                .field("upload_max_kbps", wan_bandwidth["upload_max_kbps"])
                .field("download_max_kbps", wan_bandwidth["download_max_kbps"])
                .field("upload_max_mbps", wan_bandwidth["upload_max_mbps"])
                .field("download_max_mbps", wan_bandwidth["download_max_mbps"])
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
