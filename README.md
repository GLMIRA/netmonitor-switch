# NetMonitor Switch 🔌

Monitoramento em tempo real de switches TP-Link (SG3428/SG series) com coleta de métricas de CPU, portas, temperatura, MAC table e logs do sistema.

## 🚀 Features

- ✅ **Monitoramento de CPU** - Uso em tempo real com status (normal/warning/critical)
- ✅ **Análise de Tráfego de Portas** - RX/TX em bytes e pacotes
- ✅ **Status de Portas** - Link up/down, estado, velocidade
- ✅ **Rastreamento de Dispositivos** - Tabela MAC com contagem por porta
- ✅ **System Health** - Temperatura, fan status, uptime
- ✅ **Logs Centralizados** - Coleta e classificação por severidade
- ✅ **InfluxDB Integration** - Armazenamento time-series
- ✅ **Grafana Dashboards** - Visualização de métricas

## 📊 Stack Tecnológica

- **Python 3.13** - Linguagem principal
- **InfluxDB 2.7** - Banco de dados time-series
- **Grafana** - Dashboards e visualização
- **Docker Compose** - Orquestração de containers
- **TP-Link API** - Comunicação com switches SG series

## 🏗️ Estrutura do Projeto

```
netmonitor-switch/
src/
├── auth/
│   └── auth_switch.py
├── collectors/                    
│   ├── cpu_info.py
│   ├── port_util.py
│   ├── status_port.py
│   ├── mac_address.py             
│   ├── system_time.py
│   └── logs_switch.py
├── processors/
│   ├── cpu_processor.py
│   ├── port_processors.py
│   ├── mac_address.py             
│   ├── system_processor.py
│   └── logs_processors.py
├── database/
│   └── influx_db.py
├── utils/
│   └── logger.py
└── main.py

```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd network-monitor
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To start the network monitoring system, run the following command:
```
python src/main.py
```

## Configuration

Configuration settings can be adjusted in the `config/settings.yaml` file. Additionally, you can set environment variables as specified in the `.env.example` file.

## Testing

To run the tests, use the following command:
```
pytest tests/
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.