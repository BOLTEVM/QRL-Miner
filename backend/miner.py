import asyncio
import json
import logging
import os
import subprocess
import time
import urllib.request
import zipfile
import shutil
from typing import Dict, Any, Optional

import re
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("miner")

XMRIG_VERSION = "6.26.0"
XMRIG_URL = f"https://github.com/xmrig/xmrig/releases/download/v{XMRIG_VERSION}/xmrig-{XMRIG_VERSION}-gcc-win64.zip"
BIN_DIR = os.path.join(os.path.dirname(__file__), "bin")
XMRIG_EXE = os.path.join(BIN_DIR, "xmrig.exe")

class QRLMiner:
    def __init__(self, host: str, port: int, address: str, worker_name: str = "bqrl_worker", threads: int = 1, use_tls: bool = False):
        self.host = host
        self.port = port
        self.address = address
        self.worker_name = worker_name
        self.threads = threads
        self.use_tls = use_tls
        self.running = False
        self.hashrate = 0
        self.shares_accepted = 0
        self.shares_rejected = 0
        self.last_error = None
        self._process: Optional[subprocess.Popen] = None
        self._telemetry_task: Optional[asyncio.Task] = None
        self._log_pipe_task: Optional[asyncio.Task] = None
        self.log_queue = []
        self.last_job = None
        self.connection_state = "IDLE"

    def add_log(self, category: str, message: str, custom_time: str = None):
        timestamp = custom_time if custom_time else time.strftime("%H:%M:%S")
        log_entry = {"time": timestamp, "cat": category, "msg": message}
        self.log_queue.append(log_entry)
        if len(self.log_queue) > 100:
            self.log_queue.pop(0)
        logger.info(f"[{category}] {message}")

    def ensure_binary(self):
        if os.path.exists(XMRIG_EXE):
            logger.info("XMRig substrate found.")
            return True

        logger.info("XMRig substrate missing. Deploying from GitHub...")
        os.makedirs(BIN_DIR, exist_ok=True)
        zip_path = os.path.join(BIN_DIR, "xmrig.zip")

        try:
            # Download
            with urllib.request.urlopen(XMRIG_URL) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the exe in the zip (it's inside a folder)
                for member in zip_ref.namelist():
                    if member.endswith("xmrig.exe"):
                        with zip_ref.open(member) as source, open(XMRIG_EXE, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        break
            
            os.remove(zip_path)
            self.add_log("DEBUG", "XMRig substrate successfully deployed to cluster.")
            return True
        except Exception as e:
            self.add_log("ERROR", f"Deployment failed: {e}")
            self.last_error = f"Binary deployment failed: {e}"
            return False

    async def run(self):
        if not self.ensure_binary():
            return

        self.running = True
        # Launch XMRig
        cmd = [
            XMRIG_EXE,
            "--algo", "rx/0",
            "--url", f"{self.host}:{self.port}",
            "--user", self.address,
            "--pass", "x",
            "--threads", str(self.threads),
            "--http-port", "16000",
            "--no-color",
            "--cpu",
            "--api-worker-id", self.worker_name
        ]
        if self.use_tls:
            cmd.append("--tls")

        try:
            logger.info(f"Launching substrate: {' '.join(cmd)}")
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Start background tasks
            self._telemetry_task = asyncio.create_task(self.monitor_telemetry())
            self._log_pipe_task = asyncio.create_task(self.pipe_substrate_logs())
            
            # Keep running until process ends or stopped
            while self.running:
                if self._process.poll() is not None:
                    self.add_log("ERROR", "Substrate process terminated unexpectedly.")
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            self.last_error = str(e)
        finally:
            self.stop_mining()
            self.connection_state = "IDLE"

    async def pipe_substrate_logs(self):
        """Asynchronously read and parse XMRig stdout"""
        if not self._process or not self._process.stdout:
            return

        # Simple Regex to extract XMRig log components
        # Format: [2026-04-09 16:16:18.289]  cat   message
        log_pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2}\s(\d{2}:\d{2}:\d{2})\.\d{3})\]\s+(\w+)\s+(.+)")

        while self.running and self._process.poll() is None:
            # We use a small timeout to not block the loop completely
            line = await asyncio.get_event_loop().run_in_executor(None, self._process.stdout.readline)
            if not line:
                break
            
            decoded_line = line.decode().strip()
            if not decoded_line:
                continue

            match = log_pattern.search(decoded_line)
            if match:
                _, time_str, cat, msg = match.groups()
                # Map XMRig categories to our UI categories
                cat_lower = cat.lower()
                ui_cat = "NET" if cat_lower in ["net", "config"] else "PROC" if cat_lower in ["cpu", "miner"] else "DEBUG"
                # Strip ANSI escape codes if any (XMRig is started with --no-color but just in case)
                clean_msg = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', msg)
                self.add_log(ui_cat, clean_msg, custom_time=time_str)
            else:
                # Fallback for lines that don't match the standard pattern (e.g. startup credits)
                clean_line = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', decoded_line)
                if "*" in clean_line or "ABOUT" in clean_line or "LIBS" in clean_line:
                    self.add_log("DEBUG", clean_line.replace("*", "").strip())

    async def monitor_telemetry(self):
        while self.running:
            try:
                # Poll XMRig API
                req = urllib.request.Request("http://127.0.0.1:16000/1/summary")
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    new_hashrate = int(data.get("hashrate", {}).get("total", [0])[0])
                    
                    if self.connection_state != "CONNECTED" and new_hashrate > 0:
                        self.connection_state = "CONNECTED"
                        # Status change is real data
                        logger.info(f"Mining confirmed: {new_hashrate} H/s")

                    self.hashrate = new_hashrate
                    self.shares_accepted = data.get("results", {}).get("shares_good", 0)
                    
                    # Watch for new jobs
                    current_job = data.get("results", {}).get("job_id")
                    if current_job and current_job != self.last_job:
                        self.last_job = current_job
                        # Real data only: we don't log "New workload received" here anymore 
                        # as it will come from the XMRig stdout pipe naturally.

            except Exception as e:
                # XMRig might still be initializing
                pass
            await asyncio.sleep(2)

    def stop_mining(self):
        self.running = False
        if self._telemetry_task:
            self._telemetry_task.cancel()
            self._telemetry_task = None
        
        if self._process:
            logger.info("Terminating XMRig substrate...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        
        self.hashrate = 0
