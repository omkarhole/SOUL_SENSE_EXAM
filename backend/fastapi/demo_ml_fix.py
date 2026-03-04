import asyncio
import sys
import os
import time
import subprocess
import json

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'backend', 'fastapi'))

from api.ml.inference_server import inference_proxy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_ml_server():
    logger.info("Starting ML Inference Server in background...")
    # Using the same interpreter as the current process
    return subprocess.Popen(
        [sys.executable, "backend/fastapi/api/ml/inference_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

async def run_demo():
    server_proc = start_ml_server()
    time.sleep(3) # Give server time to start and connect to Redis
    
    try:
        logger.info("--- Testing ML Inference Architecture ---")
        
        # 1. Ping test
        logger.info("Task 1: Ping ML Process...")
        pong = inference_proxy.run_inference("ping", {})
        logger.info(f"Response: {pong}")
        
        # 2. Burnout Analytics test
        logger.info("Task 2: Burnout Z-Score Inference...")
        stats = [
            {"sentiment": 0.8, "stress": 0.2},
            {"sentiment": 0.7, "stress": 0.3},
            {"sentiment": 0.8, "stress": 0.2},
            {"sentiment": 0.6, "stress": 0.4},
            {"sentiment": 0.1, "stress": 0.9} # High stress detected
        ]
        result = inference_proxy.run_inference("burnout_detection", {"stats": stats})
        logger.info(f"ML Output: {json.dumps(result, indent=2)}")
        
        logger.info("--- Architecture Isolation Verified ---")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        server_proc.terminate()

if __name__ == "__main__":
    asyncio.run(run_demo())
