"""Download BiRefNet model weights.

Run:  python download_model.py
Uses hf-mirror.com by default (China-friendly). If that fails, edit the
HF_ENDPOINT line below or run with an env var:  set HF_ENDPOINT=https://huggingface.co
"""

import os
import sys

# ---- Configure endpoint here ----
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
endpoint = os.environ["HF_ENDPOINT"]
print(f"Using endpoint: {endpoint}")
print("Downloading BiRefNet_HR-matting (model.safetensors ~900MB)...")
print("Progress bar below. If it stalls, Ctrl+C and retry,")
print("or set HF_ENDPOINT=https://huggingface.co with a proxy.")
print("-" * 60)

# Imported here (not at top) so the banner above prints before the slow
# huggingface_hub import — keeps the console responsive on first run.
from huggingface_hub import snapshot_download  # noqa: E402

try:
    path = snapshot_download(
        repo_id="ZhengPeng7/BiRefNet_HR-matting",
        allow_patterns=[
            "config.json",
            "birefnet.py",
            "BiRefNet_config.py",
            "model.safetensors",
            "handler.py",
        ],
        endpoint=endpoint,
    )
    print("-" * 60)
    print(f"DONE -> {path}")
    print("Files:", os.listdir(path))
    print("Now run start.bat to launch the app.")
except Exception as e:
    print("-" * 60)
    print(f"FAILED: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Retry: python download_model.py")
    print("  2. Switch endpoint: edit HF_ENDPOINT in this file,")
    print("     or:  set HF_ENDPOINT=https://huggingface.co")
    print("  3. Use a proxy for huggingface.co")
    sys.exit(1)
