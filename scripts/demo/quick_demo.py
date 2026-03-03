import logging
import json
from datetime import datetime, timezone
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_demo():
    """Compute burnout detection Z‑scores directly without DB or Redis."""
    # Simulated stats (same as previous demo)
    stats = [
        {"sentiment": 0.8, "stress": 0.2},
        {"sentiment": 0.7, "stress": 0.3},
        {"sentiment": 0.8, "stress": 0.2},
        {"sentiment": 0.6, "stress": 0.4},
        {"sentiment": 0.1, "stress": 0.9},  # current entry
    ]

    sentiments = [s["sentiment"] for s in stats]
    stresses = [s["stress"] for s in stats]

    baseline_sent_mean = np.mean(sentiments[:-1])
    baseline_sent_std = np.std(sentiments[:-1]) or 1.0
    baseline_stress_mean = np.mean(stresses[:-1])
    baseline_stress_std = np.std(stresses[:-1]) or 1.0

    current_sent = sentiments[-1]
    current_stress = stresses[-1]

    z_sent = (current_sent - baseline_sent_mean) / baseline_sent_std
    z_stress = (current_stress - baseline_stress_mean) / baseline_stress_std

    result = {
        "z_sentiment": float(z_sent),
        "z_stress": float(z_stress),
        "baseline_sent_mean": float(baseline_sent_mean),
        "baseline_stress_mean": float(baseline_stress_mean),
        "is_burnout": bool(z_sent < -1.5 and z_stress > 1.5),
        "is_crisis": bool(z_sent < -2.5 or z_stress > 2.5),
        "timestamp": datetime.now(timezone.utc).isoformat(),

    }
    logger.info("Burnout detection result:\n" + json.dumps(result, indent=2))

if __name__ == "__main__":
    run_demo()
