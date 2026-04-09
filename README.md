<p align="center">
  <img src="0logov3.png" width="400" alt="QRL Miner Logo" />
</p>

# Quantum Resistant Ledger (QRL) Miner Core

A sophisticated, high-performance mining dashboard designed for the future of post-quantum cryptography. This project wraps the world-class **XMRig** substrate in a real-time, event-driven architecture featuring a high-fidelity CLI terminal and advanced protocol configuration.

## 🚀 Key Features

- **Real-time Substrate Terminal**: A CRT-inspired CLI that pipes live data directly from the XMRig process. No mock data—just pure, low-level mining telemetry.
- **Advanced Tuning**: Direct support for **Huge Pages** and **MSR Mod** to maximize RandomX hashrate on modern CPU architectures.
- **Protocol Stabilization**: Out-of-the-box support for multiple QRL pools with manual SSL/TLS toggle for encrypted stratum handshakes.
- **Hybrid Stack**: Built using a high-concurrency **FastAPI** backend and a reactive, lightweight **Preact** frontend managed via Bun.

## 🛠️ Project Structure

```text
├── backend/          # FastAPI server & XMRig wrapper
│   ├── bin/          # Substrate executable (auto-deployed)
│   ├── main.py       # API & WebSocket gateways
│   └── miner.py      # Substrate life-cycle manager (Real-time I/O)
└── frontend/         # Preact + Vite Dashboard
    ├── src/          # UI Components & Design System
    └── index.html    # Entry point
```

## 🏁 Quick Start

### Prerequisites
- **Python 3.10+**
- **Bun** (for frontend development)
- **Administrator Privileges** (required for Hardware Tuning)

### 1. Initialize Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install fastapi uvicorn websockets
python main.py
```

### 2. Initialize Frontend
```bash
cd frontend
bun install
bun dev
```

### 3. Start Mining
1. Open `http://localhost:3699` in your browser.
2. Enter your QRL Wallet Address.
3. Select your preferred cluster node (MiningOcean/HeroMiners).
4. Hit **Initialize Miner**.

## 🛡️ Security & Privacy
- **Encrypted Straturm**: Toggle SSL/TLS to bypass local ISP filtering.
- **No Private Keys**: This miner never asks for your private keys; it only requires your public wallet address.

---
<p align="center">
  <i>Developed for the BOLTEVM Ecosystem.</i>
</p>
