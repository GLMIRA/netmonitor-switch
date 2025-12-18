"""Configurações do sistema de monitoramento."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações do monitor."""

    # Switch
    SWITCH_IP = os.getenv("SWITCH_IP")
    SWITCH_USER = os.getenv("SWITCH_USER")
    SWITCH_PASSWORD = os.getenv("SWITCH_PASSWORD")

    # Intervalos (segundos)
    COLLECTION_INTERVAL = 300  # 5 minutos
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
