"""Configurações do sistema de monitoramento."""

import os
from dotenv import load_dotenv

load_dotenv()


class ConfigSwitch:
    """Configurações do monitor."""

    # Switch
    SWITCH_IP = os.getenv("SWITCH_IP")
    SWITCH_USER = os.getenv("SWITCH_USER")
    SWITCH_PASSWORD = os.getenv("SWITCH_PASSWORD")

    # Intervalos (segundos)
    COLLECTION_INTERVAL = 40  # 40 segundos
    RETRY_INTERVAL = 60  # 1 minuto após erro
    REQUEST_DELAY = 2  # Delay entre requests

    # Limites
    MAX_CONSECUTIVE_ERRORS = 5

    @classmethod
    def validate(cls):
        """Valida se todas as configs necessárias existem."""
        required = ["SWITCH_IP", "SWITCH_USER", "SWITCH_PASSWORD"]
        missing = [k for k in required if not getattr(cls, k)]

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        return True


class ConfigRouter:
    """Config for Router"""

    ROUTER_IP = os.getenv("ROUTER_IP")
    ROUTER_USER = os.getenv("ROUTER_USER")
    ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")

    COLLECTION_INTERVAL = 40  # 40 segundos
    RETRY_INTERVAL = 60  # 1 minuto após erro
    REQUEST_DELAY = 6  # Delay entre requests

    MAX_CONSECUTIVE_ERRORS = 5

    @classmethod
    def validate(cls):
        """Validate required router configs."""
        required = ["ROUTER_IP", "ROUTER_USER", "ROUTER_PASSWORD"]
        missing = [k for k in required if not getattr(cls, k)]

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        return True
