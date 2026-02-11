"""Base collector for router data.

This module coordinates all router data collection and processing,
integrating host information and WAN connection data collectors.
"""

import requests
from typing import Dict, Any
from src.utils.logger import get_logger
from src.collectors.router.host import collect_host_info
from src.collectors.router.wan import collect_wan_info
from src.processors.router.host_summary import process_host_summary
from src.processors.router.host_devices import process_host_devices
from src.processors.router.wan import process_wan_status, process_wan_bandwidth


logger = get_logger(__name__)


class DataCollectorRouter:
    """Router data collector integrating all collection and processing."""

    def __init__(self, router_ip: str, session: requests.Session):
        """Initialize the router collector.

        Args:
            router_ip: IP address of the router.
            session: Authenticated session object.
        """
        self.router_ip = router_ip
        self.session = session
        self.logger = get_logger(__name__)

    def collect_host_info(self) -> dict:
        """Collect host information from router.

        Returns:
            Raw host data from API.
        """
        self.logger.debug("Collecting host info...")
        host_info = collect_host_info(self.router_ip, self.session)
        return host_info

    def collect_wan_info(self) -> dict:
        """Collect WAN connection information from router.

        Returns:
            Raw WAN data from API.
        """
        self.logger.debug("Collecting WAN info...")
        wan_info = collect_wan_info(self.router_ip, self.session)
        return wan_info

    def collect_all(self) -> dict:
        """Collect all raw data from router.

        Returns:
            Dictionary with raw data:
                - host_info: Raw host data from API
                - wan_info: Raw WAN data from API
                - error: Error message if collection failed (optional)
        """
        self.logger.info("Starting router data collection")
        data = {}

        try:
            data["host_info"] = self.collect_host_info()
            data["wan_info"] = self.collect_wan_info()

            # Check for errors in collected data
            if "error" in data["host_info"]:
                self.logger.warning(
                    f"Host info collection error: {data['host_info']['error']}"
                )
            if "error" in data["wan_info"]:
                self.logger.warning(
                    f"WAN info collection error: {data['wan_info']['error']}"
                )

            self.logger.info("Router data collection completed")
            return data

        except Exception as error:
            self.logger.error(f"Error collecting router data: {error}", exc_info=True)
            data["error"] = str(error)
            return data

    def process_all(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all raw router data.

        Args:
            raw_data: Dictionary with raw data from collect_all().

        Returns:
            Dictionary with processed data:
                - host_summary: Aggregated host metrics
                - host_devices: List of active devices
                - wan_status: WAN connection status
                - wan_bandwidth: WAN bandwidth metrics
                - error: Error message if processing failed (optional)
        """
        self.logger.info("Starting router data processing")
        processed = {}

        try:
            # Process host information
            if "host_info" in raw_data and "error" not in raw_data["host_info"]:
                processed["host_summary"] = process_host_summary(raw_data["host_info"])
                processed["host_devices"] = process_host_devices(raw_data["host_info"])
                self.logger.debug(
                    f"Processed {len(processed['host_devices'])} active devices"
                )
            else:
                self.logger.warning(
                    "Skipping host info processing due to collection error"
                )
                processed["host_summary"] = {}
                processed["host_devices"] = []

            # Process WAN information
            if "wan_info" in raw_data and "error" not in raw_data["wan_info"]:
                processed["wan_status"] = process_wan_status(raw_data["wan_info"])
                processed["wan_bandwidth"] = process_wan_bandwidth(raw_data["wan_info"])
                self.logger.debug(
                    f"Processed WAN status: {processed['wan_status'].get('connection_status')}"
                )
            else:
                self.logger.warning(
                    "Skipping WAN info processing due to collection error"
                )
                processed["wan_status"] = {}
                processed["wan_bandwidth"] = {}

            self.logger.info("Router data processing completed")
            return processed

        except Exception as error:
            self.logger.error(f"Error processing router data: {error}", exc_info=True)
            processed["error"] = str(error)
            return processed
