"""Entry point do sistema de monitoramento."""

from src.utils.monitor import NetworkMonitor


def main():
    """Inicia o monitor."""
    monitor = NetworkMonitor()
    monitor.run()
    return 0


if __name__ == "__main__":
    exit(main())
