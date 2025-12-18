"""Monitor principal do switch."""

import time
import gc
from datetime import datetime

from src.auth.auth_switch import switch_auth
from src.collectors.collector import DataCollector
from src.utils.config import Config
from src.database.influx_db import InfluxDB  # ← ADICIONAR
from src.utils.logger import setup_logging, get_logger


class SwitchMonitor:
    """Monitor de switch TP-Link."""

    def __init__(self):
        """Inicializa o monitor."""
        setup_logging()
        self.logger = get_logger(__name__)

        # Validar configurações
        Config.validate()

        self.switch_ip = Config.SWITCH_IP
        self.username = Config.SWITCH_USER
        self.password = Config.SWITCH_PASSWORD

        # Estado
        self.auth = None
        self.cycle_count = 0
        self.error_count = 0

        self.logger.info(f"SwitchMonitor initialized for {self.switch_ip}")

    def authenticate(self) -> bool:
        """Autentica no switch."""
        self.logger.info("Authenticating to switch...")
        auth_result = switch_auth(self.switch_ip, self.username, self.password, "write")

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
            from src.collectors.collectors_cpu import get_cpu_info

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
            db = InfluxDB()

            # Escrever cada tipo de dado
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
        cycle_start = time.time()
        self.cycle_count += 1

        self.logger.info("=" * 60)
        self.logger.info(
            f"CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.logger.info("=" * 60)

        try:
            # 1. Garantir autenticação
            if not self.ensure_auth():
                self.error_count += 1
                self.logger.error(
                    f"Auth failed (error {self.error_count}/{Config.MAX_CONSECUTIVE_ERRORS})"
                )
                return False

            # 2. Coletar dados
            collector = DataCollector(self.switch_ip, self.auth)
            data = collector.collect_all()

            if "error" in data:
                self.error_count += 1
                self.logger.error(
                    f"Collection failed (error {self.error_count}/{Config.MAX_CONSECUTIVE_ERRORS})"
                )
                return False

            # 3. Salvar dados
            self.save_data(data)

            # 4. Limpar memória
            gc.collect()

            # 5. Resetar erros
            self.error_count = 0

            # 6. Log de sucesso
            cycle_duration = time.time() - cycle_start
            self.logger.info(
                f"Cycle #{self.cycle_count} completed in {cycle_duration:.2f}s"
            )
            self._log_summary(data)

            return True

        except Exception as e:
            self.error_count += 1
            self.logger.error(
                f"Unexpected error (error {self.error_count}/{Config.MAX_CONSECUTIVE_ERRORS}): {e}",
                exc_info=True,
            )
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

    def run(self):
        """Loop principal."""
        self.logger.info(
            f"Starting monitoring loop (interval: {Config.COLLECTION_INTERVAL}s)..."
        )

        while True:
            try:
                success = self.run_cycle()

                # Parar se muitos erros
                if self.error_count >= Config.MAX_CONSECUTIVE_ERRORS:
                    self.logger.critical(
                        f"Too many errors ({Config.MAX_CONSECUTIVE_ERRORS}), stopping..."
                    )
                    break

                # Aguardar próximo ciclo
                interval = (
                    Config.COLLECTION_INTERVAL if success else Config.RETRY_INTERVAL
                )
                self.logger.info(f"Waiting {interval}s for next cycle...")
                time.sleep(interval)

            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user (Ctrl+C)")
                break
            except Exception as e:
                self.logger.error(f"Fatal error: {e}", exc_info=True)
                time.sleep(Config.RETRY_INTERVAL)
