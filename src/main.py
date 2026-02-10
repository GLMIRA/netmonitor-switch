"""Entry point do sistema de monitoramento."""

from src.utils.monitor import SwitchMonitor


def main():
    """Inicia o monitor."""
    monitor = SwitchMonitor()
    monitor.run()
    return 0


if __name__ == "__main__":
    exit(main())
