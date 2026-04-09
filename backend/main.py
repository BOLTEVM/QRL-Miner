from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from miner import QRLMiner
import os
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="QRL Premium Miner API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models to fix 422 errors
class StartRequest(BaseModel):
    address: str
    threads: int = 1
    host: str = "qrl.miningocean.org"
    port: int = 3333
    use_tls: bool = False


# Global miner instance
miner_instance = QRLMiner(
    host="qrl.miningocean.org", # Verified active pool for 2026
    port=3333, 
    address="Q0105007a9b2d5c63770e481ab66dbf0f87faefcc4a8b78990390919198642273087037f",
    threads=2
)


@app.get("/status")
async def get_status():
    import psutil
    physical_cores = psutil.cpu_count(logical=False) or 1
    return {
        "running": miner_instance.running,
        "hashrate": miner_instance.hashrate,
        "shares_accepted": miner_instance.shares_accepted,
        "address": miner_instance.address,
        "threads": miner_instance.threads,
        "max_threads": os.cpu_count() or 1,
        "physical_threads": physical_cores
    }


@app.post("/start")
async def start_miner(req: StartRequest):
    logger.info(f"Start request received for pool {req.host}:{req.port}")
    if miner_instance.running:
        return {"success": False, "message": "Miner already running"}
    
    miner_instance.address = req.address
    miner_instance.threads = req.threads
    miner_instance.host = req.host
    miner_instance.port = req.port
    miner_instance.use_tls = req.use_tls
    
    # Run miner in background task
    asyncio.create_task(miner_instance.run())
    return {"success": True, "message": f"Initializing connection to {req.host}..."}


@app.post("/stop")
async def stop_miner():
    miner_instance.stop_mining()
    return {"success": True, "message": "Miner shutdown sequence initiated"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Hardware telemetry WebSocket connected")
    try:
        while True:
            stats = {
                "hashrate": miner_instance.hashrate,
                "shares": miner_instance.shares_accepted,
                "running": miner_instance.running,
                "threads": miner_instance.threads,
                "logs": miner_instance.log_queue
            }
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("Hardware telemetry WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
