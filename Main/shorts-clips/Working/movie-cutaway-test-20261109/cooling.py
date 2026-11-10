"""Let the admitted GPU cool between bounded work units without changing its limits."""
import os
import subprocess
import time

def cool():
    deadline = time.monotonic() + 150
    while True:
        value = subprocess.check_output([
            "nvidia-smi", "-i", os.environ.get("CLIPPING_GUARD_GPU_INDEX", "0"),
            "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits",
        ], text=True, timeout=6).strip()
        if int(value) <= 75:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(f"GPU did not cool to 75 C between units (last: {value} C)")
        time.sleep(5)
