# Avtomatika: Full Feature Showcase

EN | [RU](./README_RU.md)

This project provides a comprehensive demonstration of the **Avtomatika HLN (Hierarchical Logic Network)** ecosystem. it covers all key architectural patterns: from simple tasks to nested workflows, parallel execution, and automated scheduling.

## 🏗 System Architecture

The example deploys a full-featured distributed environment:

![Main Blueprint](docs/images/full_showcase_graph.png)

1.  **Orchestrator**: The central engine managing the `full_showcase` blueprint.
2.  **GPU Worker**: A high-performance worker for "heavy" tasks (transcoding).
3.  **CPU Workers**: Two workers for file analysis (one reliable, one intentionally glitchy for reputation testing).

### 🪆 Sub-process logic
The `metadata_enrichment` sub-blueprint:
![Sub Blueprint](docs/images/metadata_enrichment_graph.png)

4.  **Scheduler**: Native scheduler that triggers maintenance tasks periodically.
5.  **Webhook Receiver**: External service demonstrating real-time job status notifications.
6.  **Infrastructure**: 
    *   **Redis**: Real-time state storage and task queues.
    *   **PostgreSQL**: Long-term history and audit trails.
    *   **MinIO (S3)**: Heavy payload offloading.
    *   **VictoriaMetrics & Grafana**: High-performance monitoring stack.
    *   **Jaeger**: Distributed tracing (OpenTelemetry).

## 🌟 Key Features in this Example

### 1. Native Scheduler ⏰
The Orchestrator automatically loads configuration from `schedules.toml`. The example includes a `maintenance_task` that runs every minute to execute a cleanup blueprint.

### 2. Nested Workflows (Sub-Blueprints) 🪆
The `full_showcase` process triggers a child blueprint `metadata_enrichment`. This demonstrates how to break down complex business logic into isolated, reusable blocks.

### 3. Parallelism (Fan-Out/Fan-In) 🚀
Demonstrates simultaneous execution of multiple file analysis tasks. The Orchestrator waits for all parallel branches to complete and aggregates their results into a single context.

### 4. Smart Dispatching 🧠
Shows various worker selection strategies:
*   `default`: Balancing based on skill hot-cache.
*   `best_value`: Selecting workers based on price/reputation ratio.
*   `round_robin`: Sequential task distribution.

### 5. Webhook Integration 📡
The `client.py` registers a `webhook_url` during job creation. The Orchestrator sends a POST request to the `webhook_receiver` immediately upon job completion or failure.

## 🚀 Quick Start (Docker)

The fastest way to see everything in action is using Docker Compose.

1.  **Launch the Stack**:
    ```bash
    cd projects/avtomatika_full_example
    docker compose up -d --build
    ```

2.  **Run the Test Client**:
    The script will create a job and display an interactive progress bar:
    ```bash
    # Virtual environment is recommended
    python3 -m venv .venv
    source .venv/bin/activate
    pip install aiohttp
    python3 client.py
    ```

## 📊 Monitoring & Tools

Once running, the following interfaces are available:
*   **Grafana**: [http://localhost:3000](http://localhost:3000) (Pre-configured "Avtomatika Overview" dashboard).
*   **Jaeger (Traces)**: [http://localhost:16686](http://localhost:16686).
*   **API Docs (Swagger)**: [http://localhost:8080/_public/docs](http://localhost:8080/_public/docs).
*   **Metrics (Prometheus)**: [http://localhost:8080/_public/metrics](http://localhost:8080/_public/metrics).

## 📂 File Structure

*   `full_example.py`: Orchestrator entry point.
*   `config.py`: Configuration loading logic.
*   `blueprints/`: Package containing business logic definitions (blueprints).
*   `workers/`: Directory with example workers (GPU, Reliable CPU, Unreliable CPU).
*   `webhook_receiver.py`: Webhook notification server.
*   `schedules.toml`: Periodic task configuration.
*   `example_clients.toml`: API key and access control settings.
*   `ops/`: Monitoring configurations (VictoriaMetrics, Grafana).

---
*Maintained by Dmitrii Gagarin aka madgagarin.*
