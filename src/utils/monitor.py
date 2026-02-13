"""Network monitoring system for switch and router."""

import time
import gc
from datetime import datetime

import requests

from src.auth import switch
from src.auth import router
from src.collectors.router.base import DataCollectorRouter
from src.utils.config import ConfigSwitch, ConfigRouter
from src.database.client import InfluxDBSwitch, InfluxDBRouter
from src.utils.logger import setup_logging, get_logger
from src.collectors.switch.base import DataCollector
from src.collectors.switch.cpu import get_cpu_info


class NetworkMonitor:
    """Main network monitor coordinating switch and router monitoring."""

    def __init__(self):
        """Initialize the network monitor."""
        setup_logging()
        self.logger = get_logger(__name__)

        ConfigSwitch.validate()
        ConfigRouter.validate()

        self.switch_monitor = SwitchMonitor()
        self.router_monitor = RouterMonitor()

        self.cycle_count = 0
        self.logger.info("NetworkMonitor initialized")

    def run(self):
        """Main monitoring loop."""
        self.logger.info("Starting network monitoring loop...")

        while True:
            try:
                self.cycle_count += 1
                self.logger.info("=" * 60)
                self.logger.info(
                    f"CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.logger.info("=" * 60)

                switch_success = self.switch_monitor.run_cycle()
                router_success = self.router_monitor.run_cycle()

                gc.collect()

                if not switch_success and not router_success:
                    self.logger.error("Both switch and router collection failed")
                    interval = max(
                        ConfigSwitch.RETRY_INTERVAL, ConfigRouter.RETRY_INTERVAL
                    )
                else:
                    interval = min(
                        ConfigSwitch.COLLECTION_INTERVAL,
                        ConfigRouter.COLLECTION_INTERVAL,
                    )

                self.logger.info(f"Waiting {interval}s for next cycle...")
                time.sleep(interval)

            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user (Ctrl+C)")
                break
            except Exception as e:
                self.logger.error(f"Fatal error: {e}", exc_info=True)
                time.sleep(60)


class SwitchMonitor:
    """Monitor de switch TP-Link."""

    def __init__(self):
        """Inicializa o monitor."""
        self.logger = get_logger(__name__)

        self.switch_ip = ConfigSwitch.SWITCH_IP
        self.username = ConfigSwitch.SWITCH_USER
        self.password = ConfigSwitch.SWITCH_PASSWORD

        self.auth = None
        self.error_count = 0

        self.logger.info(f"SwitchMonitor initialized for {self.switch_ip}")

    def authenticate(self) -> bool:
        """Autentica no switch."""
        self.logger.info("Authenticating to switch...")
        auth_result = switch.switch_auth(
            self.switch_ip, self.username, self.password, "write"
        )

        if "error" in auth_result:
            self.logger.error(f"Authentication failed: {auth_result['error']}")
            return False

        self.auth = auth_result
        self.logger.info("Authentication successful!")
        return True

    def test_auth(self) -> bool:
        """Testa se a autenticação ainda é válida."""

        if self.auth is None:
            return False

        try:

            cpu_raw = get_cpu_info(self.switch_ip, self.auth)

            if "error" in cpu_raw:
                self.logger.warning("Auth test failed, session expired")
                self.auth = None
                return False

            return True

        except Exception as e:
            self.logger.error(f"Auth test exception: {e}")
            self.auth = None
            return False

    def ensure_auth(self) -> bool:
        """Garante que está autenticado."""
        if not self.test_auth():
            return self.authenticate()
        return True

    def save_data(self, data: dict):
        """Salva dados no InfluxDB."""
        try:
            db = InfluxDBSwitch()

            db.write_cpu_data(data.get("cpu", {}))
            db.write_system_data(data.get("system", {}))
            db.write_port_data(data.get("ports", {}))
            db.write_mac_data(data.get("mac", {}))
            db.write_log_data(data.get("logs", {}))

            db.close()
            self.logger.info("Data saved to InfluxDB successfully")

        except Exception as e:
            self.logger.error(f"Error saving data to InfluxDB: {e}", exc_info=True)

    def run_cycle(self) -> bool:
        """Executa um ciclo de coleta."""
        try:
            if not self.ensure_auth():
                self.error_count += 1
                self.logger.error(f"Switch auth failed (error {self.error_count})")
                return False

            collector = DataCollector(self.switch_ip, self.auth)
            data = collector.collect_all()

            if "error" in data:
                self.error_count += 1
                self.logger.error(
                    f"Switch collection failed (error {self.error_count})"
                )
                return False

            self.save_data(data)
            self.error_count = 0

            self.logger.info("Switch cycle completed successfully")
            return True

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Switch unexpected error: {e}", exc_info=True)
            return False

    def _log_summary(self, data: dict):
        """Log resumo do ciclo."""
        ports_connected = len(
            [p for p in data["ports"].get("ports", []) if p.get("is_connected")]
        )
        total_ports = len(data["ports"].get("ports", []))
        total_macs = len(data["mac"].get("mac_addresses", []))
        total_logs = len(data["logs"].get("logs", []))

        self.logger.info(
            f"Summary: CPU={data['cpu'].get('cpu_usage_percent')}%, "
            f"Temp={data['system'].get('temperature')}°C, "
            f"Ports={ports_connected}/{total_ports}, "
            f"MACs={total_macs}, "
            f"Logs={total_logs}"
        )


class RouterMonitor:
    """Monitoramento do Roteador"""

    def __init__(self):
        """Inicializa o monitor do router."""
        self.logger = get_logger(__name__)

        self.router_ip = ConfigRouter.ROUTER_IP
        self.username = ConfigRouter.ROUTER_USER
        self.password = ConfigRouter.ROUTER_PASSWORD

        self.session = None
        self.error_count = 0

        self.logger.info(f"RouterMonitor initialized for {self.router_ip}")

    def authenticate(self) -> bool:
        """Autentica no router."""
        self.logger.info("Authenticating to router...")
        self.session = router.get_authenticated_session(
            self.router_ip, self.username, self.password
        )

        if self.session is None:
            self.logger.error("Authentication failed")
            return False

        self.logger.info("Authentication successful!")
        return True

    def test_auth(self) -> bool:
        """Testa se a sessão ainda é válida."""
        if self.session is None:
            return False

        try:
            test_url = f"http://{self.router_ip}/api/system/HostInfo"
            response = self.session.get(test_url, timeout=3)

            if response.status_code in [401, 403, 404]:
                self.logger.warning("Session expired (auth required)")
                self.session = None
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Session test failed: {e}")
            self.session = None
            return False

    def ensure_auth(self) -> bool:
        """Garante que está autenticado."""
        if not self.test_auth():
            return self.authenticate()
        return True

    def run_cycle(self) -> bool:
        """Executa um ciclo de coleta do router."""
        try:
            if not self.ensure_auth():
                self.error_count += 1
                self.logger.error(f"Router auth failed (error {self.error_count})")
                return False

            self.logger.info("Collecting router data...")

            collector = DataCollectorRouter(self.router_ip, self.session)

            # Collect raw data
            raw_data = collector.collect_all()

            if "error" in raw_data:
                self.error_count += 1
                self.logger.error(
                    f"Router collection failed (error {self.error_count}): {raw_data['error']}"
                )
                return False

            # Process data
            processed_data = collector.process_all(raw_data)

            if "error" in processed_data:
                self.error_count += 1
                self.logger.error(
                    f"Router processing failed (error {self.error_count}): {processed_data['error']}"
                )
                return False

            # Log summary for validation
            self._log_router_summary(processed_data)

            # Save data to InfluxDB
            self.save_data(processed_data)

            self.error_count = 0
            self.logger.info("Router cycle completed successfully")
            return True

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Router error: {e}", exc_info=True)
            return False

    def _log_router_summary(self, data: dict):
        """Log summary of router data for validation.

        Args:
            data: Processed router data dictionary.
        """
        # WAN Status Summary
        wan_status = data.get("wan_status", {})
        wan_bandwidth = data.get("wan_bandwidth", {})

        if wan_status:
            self.logger.info(
                f"WAN Status: {wan_status.get('connection_status')} | "
                f"Access: {wan_status.get('access_status')} | "
                f"IPv4: {wan_status.get('ipv4_address')} | "
                f"IPv6: {wan_status.get('ipv6_address')}"
            )

        if wan_bandwidth:
            self.logger.info(
                f"Bandwidth: UP {wan_bandwidth.get('upload_current_mbps')} Mbps, "
                f"DOWN {wan_bandwidth.get('download_current_mbps')} Mbps | "
                f"Max: UP {wan_bandwidth.get('upload_max_mbps')} Mbps, "
                f"DOWN {wan_bandwidth.get('download_max_mbps')} Mbps"
            )

        # Host Summary
        host_summary = data.get("host_summary", {})

        if host_summary:
            self.logger.info(
                f"Devices: {host_summary.get('devices_online')} online / "
                f"{host_summary.get('total_devices')} total | "
                f"LAN: {host_summary.get('devices_lan')}, "
                f"WiFi 2.4GHz: {host_summary.get('devices_wifi_2_4ghz')}, "
                f"WiFi 5GHz: {host_summary.get('devices_wifi_5ghz')}"
            )

            self.logger.info(
                f"Traffic: TX {host_summary.get('total_traffic_tx_mb')} MB, "
                f"RX {host_summary.get('total_traffic_rx_mb')} MB"
            )

        # Top 3 devices by traffic
        host_devices = data.get("host_devices", [])

        if host_devices:
            top_devices = sorted(
                host_devices,
                key=lambda d: d.get("rx_mb", 0) + d.get("tx_mb", 0),
                reverse=True,
            )[:3]

            self.logger.info("Top 3 devices by traffic:")
            for i, device in enumerate(top_devices, 1):
                self.logger.info(
                    f"  {i}. {device.get('hostname')} ({device.get('ip')}) - "
                    f"RX: {device.get('rx_mb')} MB, TX: {device.get('tx_mb')} MB - "
                    f"{device.get('connection_type')}"
                )

    def save_data(self, data: dict):
        """Salva dados do router no InfluxDB."""
        try:
            db = InfluxDBRouter()

            # Add router_ip to all data structures
            if "host_summary" in data and data["host_summary"]:
                host_summary = data["host_summary"].copy()
                host_summary["router_ip"] = self.router_ip
                db.write_host_summary(host_summary)

            if "host_devices" in data and data["host_devices"]:
                host_devices = []
                for device in data["host_devices"]:
                    device_copy = device.copy()
                    device_copy["router_ip"] = self.router_ip
                    host_devices.append(device_copy)
                db.write_host_devices(host_devices)

            if "wan_status" in data and data["wan_status"]:
                wan_status = data["wan_status"].copy()
                wan_status["router_ip"] = self.router_ip
                db.write_wan_status(wan_status)

            if "wan_bandwidth" in data and data["wan_bandwidth"]:
                wan_bandwidth = data["wan_bandwidth"].copy()
                wan_bandwidth["router_ip"] = self.router_ip
                db.write_wan_bandwidth(wan_bandwidth)

            db.close()
            self.logger.info("Router data saved to InfluxDB successfully")

        except Exception as e:
            self.logger.error(
                f"Error saving router data to InfluxDB: {e}", exc_info=True
            )
