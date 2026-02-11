"""Base collector for switch data."""

from src.utils.logger import get_logger
from src.collectors.switch.cpu import get_cpu_info
from src.collectors.switch.logs import get_logs_switch
from src.collectors.switch.mac import get_mac_address_info
from src.collectors.switch.port import get_port_info
from src.collectors.switch.system_time import get_sistem_time
from src.collectors.switch.port_status import get_status_port

from src.processors.switch.cpu import process_cpu_info
from src.processors.switch.port import processor_port_trafic, processor_port_status
from src.processors.switch.mac import processor_mac_adress
from src.processors.switch.system import processor_system_info
from src.processors.switch.logs import processor_logs

logger = get_logger(__name__)


class DataCollector:
    """Collector for all switch data."""

    def __init__(self, switch_ip: str, auth: dict):
        """Initialize the data collector.

        Args:
            switch_ip: IP address of the switch
            auth: Authentication dictionary
        """
        self.switch_ip = switch_ip
        self.auth = auth
        self.logger = get_logger(__name__)

    def collect_all(self) -> dict:
        """Collect all data from the switch.

        Returns:
            dict: Dictionary containing all collected and processed data
        """
        self.logger.info("Starting data collection")

        try:
            cpu_raw = get_cpu_info(self.switch_ip, self.auth)
            if "error" in cpu_raw:
                return {"error": "Failed to collect CPU data"}

            logs_raw = get_logs_switch(self.switch_ip, self.auth)
            mac_raw = get_mac_address_info(self.switch_ip, self.auth)
            port_raw = get_port_info(self.switch_ip, self.auth)
            system_raw = get_sistem_time(self.switch_ip, self.auth)
            port_status_raw = get_status_port(self.switch_ip, self.auth)

            cpu_data = process_cpu_info(cpu_raw, self.switch_ip)
            system_data = processor_system_info(system_raw, self.switch_ip)
            port_data = processor_port_trafic(port_raw)
            port_status_data = processor_port_status(port_status_raw)
            mac_data = processor_mac_adress(mac_raw)
            logs_data = processor_logs(logs_raw, self.switch_ip)

            ports_combined = {
                "switch_ip": self.switch_ip,
                "ports": port_data.get("ports", []),
                "port_status": port_status_data.get("ports", []),
            }

            if "mac_addresses" in mac_data:
                mac_data["switch_ip"] = self.switch_ip

            result = {
                "cpu": cpu_data,
                "system": system_data,
                "ports": ports_combined,
                "mac": mac_data,
                "logs": logs_data,
            }

            self.logger.info("Data collection completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error during data collection: {e}", exc_info=True)
            return {"error": str(e)}
