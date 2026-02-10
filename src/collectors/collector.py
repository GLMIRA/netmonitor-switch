"""Módulo de coleta de dados do switch."""

import time
from typing import Dict, Any

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
from src.utils.logger import get_logger
from src.utils.config import Config  # ← CORRIGIDO (era utils.config)


class DataCollector:
    """Coletor de dados do switch."""

    def __init__(self, switch_ip: str, auth: Dict[str, Any]):
        """
        Inicializa o coletor.

        Args:
            switch_ip: IP do switch
            auth: Dados de autenticação
        """
        self.switch_ip = switch_ip
        self.auth = auth
        self.logger = get_logger(__name__)

    def _delay(self, seconds: int = None):
        """Delay entre requisições."""
        time.sleep(seconds or Config.REQUEST_DELAY)

    def collect_cpu(self) -> Dict[str, Any]:
        """Coleta dados de CPU."""
        self.logger.debug("Collecting CPU info...")
        raw = get_cpu_info(self.switch_ip, self.auth)
        processed = process_cpu_info(raw, self.switch_ip)
        self._delay()
        return processed

    def collect_system(self) -> Dict[str, Any]:
        """Coleta dados do sistema."""
        self.logger.debug("Collecting system info...")
        raw = get_sistem_time(self.switch_ip, self.auth)
        processed = processor_system_info(raw, self.switch_ip)
        self._delay()
        return processed

    def collect_ports(self) -> Dict[str, Any]:
        """Coleta dados de portas (status + tráfego)."""
        self.logger.debug("Collecting port status...")
        status_raw = get_status_port(self.switch_ip, self.auth)
        status_processed = processor_port_status(status_raw)
        self._delay()

        self.logger.debug("Collecting port traffic...")
        traffic_raw = get_port_info(self.switch_ip, self.auth)
        traffic_processed = processor_port_trafic(traffic_raw)
        self._delay(3)  # Delay maior (mais pesado)

        merged = merge_port_data(traffic_processed, status_processed)
        return merged

    def collect_mac(self) -> Dict[str, Any]:
        """Coleta tabela MAC."""
        self.logger.debug("Collecting MAC table...")
        raw = get_mac_address_info(self.switch_ip, self.auth)
        processed = processor_mac_adress(raw)
        count = count_macs_per_port(processed)
        self._delay(3)  # Delay maior (pode ser grande)

        return {
            "mac_addresses": processed.get("mac_addresses", []),
            "mac_count": count,
        }

    def collect_logs(self) -> Dict[str, Any]:
        """Coleta logs do switch."""
        self.logger.debug("Collecting switch logs...")
        raw = get_logs_switch(self.switch_ip, self.auth)
        processed = processor_logs(raw, self.switch_ip)
        self._delay(3)  # Delay maior (pode ser grande)
        return processed

    def collect_all(self) -> Dict[str, Any]:
        """
        Coleta todos os dados do switch.

        Returns:
            Dict com todos os dados coletados
        """
        try:
            data = {
                "cpu": self.collect_cpu(),
                "system": self.collect_system(),
                "ports": self.collect_ports(),
                "mac": self.collect_mac(),
                "logs": self.collect_logs(),
            }

            self.logger.info("Data collection completed successfully")
            return data

        except Exception as e:
            self.logger.error(f"Error collecting data: {e}", exc_info=True)
            return {"error": str(e)}
