# VQE Molecular Ground State

> **Domain:** Clinical Decision Support & Biomedical Computing / Quantum Chemistry
> **Standards:** CAP / CLSI / ISO Standards, VQE Quantum Chemistry Protocol

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

VQE Molecular Ground State is a dual-domain analytical platform combining:

1. **Clinical & Biomedical AI System** (`agents/`): Multi-worker evaluation engine with PHI outbound protection and cryptographic audit trails
2. **Quantum Chemistry VQE Engine** (`vqe_ground_state/`): Variational Quantum Eigensolver ground state energy computation with Jordan-Wigner mapping and UCCSD ansatz optimization

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/vqe-molecular-ground-state.git
cd vqe-molecular-ground-state

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# For development
pip install -e .
```

---

## Configuration

Set the audit secret key for production deployments:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

> **Security Note:** Without `AUDIT_SECRET_KEY` set, the system uses a development-only fallback and emits a warning. Always set this in production.

---

## CLI Usage

### 1. Single Task Evaluation (Audit)
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameters
| Argument | Description | Default |
|:---------|:------------|:--------|
| `--task-id` | Unique task identifier | `TASK-2026-001` |
| `--target` | Target identifier | `KEY-TARGET-01` |
| `--primary` | Primary metric (float) | `28.5` |
| `--secondary` | Secondary metric (float) | `14.2` |
| `--critical` | Critical flag | `False` |
| `--status` | Status descriptor | `DISCORDANT` |

---

## REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Supervisory chat |
| GET | `/api/audit/logs` | Audit trail with verification |

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=vqe_ground_state

# Run simulation benchmark
python simulator.py --tasks 1000
```

---

## Security Features

- **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Input Validation:** Metric bounds checking, NaN/infinity rejection, length limits
- **Path Traversal Protection:** File path validation for batch operations
- **ReDoS Protection:** Maximum scan length for PHI regex patterns

---

## Architecture

```
vqe-molecular-ground-state/
├── agents/                    # Clinical & Biomedical AI System
│   ├── base.py               # Security, PHI Guard, Audit Trail
│   ├── models.py             # Pydantic schemas with validation
│   ├── supervisor.py         # Multi-worker orchestrator
│   ├── workers.py            # Specialized evaluation workers
│   ├── api.py                # FastAPI REST server
│   ├── learning.py           # Bayesian calibration engine
│   ├── metrics.py            # Prometheus metrics
│   └── llm_factory.py        # LLM provider abstraction
├── vqe_ground_state/         # Quantum Chemistry VQE Engine
│   ├── models.py             # Frontier payload definitions
│   ├── agents.py             # VQE sub-agents (Jordan-Wigner, UCCSD)
│   ├── engine.py             # Core algorithmic engine
│   ├── cli.py                # VQE-specific CLI
│   └── server.py             # VQE FastAPI server
├── tests/                    # Pytest test suite
├── web/                      # Operations console (HTML)
├── cli.py                    # Main CLI entry point
├── simulator.py              # High-throughput simulation
├── enrichment.py             # VQE enrichment feature modules
├── Dockerfile                # Container build
├── docker-compose.yml        # Container orchestration
└── pyproject.toml            # Project metadata
```

---

## Container Deployment

```bash
# Build and run with Docker Compose
AUDIT_SECRET_KEY="your-secure-key" docker-compose up --build

# Or with Docker directly
docker build -t vqe-molecular-ground-state .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" vqe-molecular-ground-state
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
