
# FastAPI Health Monitoring

## Overview
This project sets up health monitoring for a FastAPI application using Prometheus for collecting metrics and Grafana for visualizing them.

## Installation
1. Install Docker and WSL on your local machine.
2. Start the FastAPI app and Grafana UI with `docker-compose up --build`.

## Code Breakdown
- **Application Code:** The `main.py` file in `root/src/app/` holds the FastAPI application code and includes Prometheus metrics integration.
- **Configuration:** The `prometheus.yml` file is in `root/prometheus_data`.
- **Docker Setup:** Place Dockerfile and `requirements.txt` in the `src` directory.
- **Docker Compose:** Place `docker-compose.yml` in the `root` directory.

### Prometheus Metrics
1. **API Usage Counters:** Counts hits from various client IPs.
2. **API Run Time:** Measures total time the API takes to handle requests.
3. **API Processing Time (T/L):** Gauges processing time per character.
4. **CPU Utilization:** Tracks CPU usage by the FastAPI app.
5. **Memory Utilization:** Monitors memory usage by the FastAPI app.
6. **Network I/O:** Logs bytes sent and received by the app.
7. **Network I/O Rate:** Monitors the rate of bytes sent and received.

These metrics are available for querying and visualization in Grafana.

## Additional Information
- If you add more code, update `requirements.txt` with new libraries and rerun `docker-compose up --build`.
- To shut down the local host, use `docker-compose down`.
- To free up memory and disk space, open the command prompt with admin access and run `wsl --shutdown` after shutting down the host.
