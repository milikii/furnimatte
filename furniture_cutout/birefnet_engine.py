"""BiRefNet_HR-matting CPU inference engine.

Official preprocessing parameters (verified against HuggingFace model card 2026-06-23):
- Input size: 2048×2048 (HR-matting training resolution)
- Normalization: ImageNet mean=[0.485,0.456,0.406] std=[0.229,0.224,0.225]
- Output: model(input)[-1].sigmoid() → [0,1]; shape (1,1,2048,2048) → [0,0] → (2048,2048)
- Deliberate deviations from official (spec-authorised):
  1. Official Resize((2048,2048)) stretches; use letterbox instead.
  2. Official .half()/FP16; use float32 per spec.
  3. torch.set_float32_matmul_precision('high') for CPU TF32 speedup.
"""

from __future__ import annotations

import torch
import numpy as np
from PIL import Image


MODEL_INPUT_SIZE = 2048  # HR-matting official training resolution


class EngineError(Exception):
    """Error from BiRefNet engine with kind classification.

    kind ∈ {"model_load", "download", "inference"}
    """

    def __init__(self, kind: str, message: str) -> None:
        self.kind = kind
        self.message = message
        super().__init__(f"[{kind}] {message}")


class BiRefNetEngine:
    """BiRefNet_HR-matting CPU inference engine.

    Load model once, reuse for multiple inferences.
    Uses letterbox preprocessing (not official stretch-resize) to satisfy
    the no-distortion requirement.
    """

    def __init__(
        self,
        model_id: str = "ZhengPeng7/BiRefNet_HR-matting",
        cache_dir: str | None = None,
        num_threads: int | None = None,
        progress_cb=None,
        hf_mirror: bool = False,
    ) -> None:
        """Store config; do NOT load model (lazy loading via load())."""
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.num_threads = num_threads
        self.progress_cb = progress_cb
        self.hf_mirror = hf_mirror
        self.model = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        """Load the model from HuggingFace or local cache.

        Uses snapshot_download first (so we can report download progress),
        then loads from the local snapshot directory.
        Raises EngineError on failure (network, disk, model compatibility).
        """
        if self.is_loaded:
            return

        # Route HuggingFace requests through hf-mirror.com (China-friendly)
        # Must be set before huggingface_hub / transformers import.
        import os
        if self.hf_mirror:
            os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

        # Set torch thread count before any model ops
        if self.num_threads is not None and self.num_threads > 0:
            torch.set_num_threads(self.num_threads)
        torch.set_num_interop_threads(1)

        try:
            from transformers import AutoModelForImageSegmentation
        except ImportError as exc:
            raise EngineError(
                "model_load",
                "transformers not installed. pip install transformers",
            ) from exc

        # Files BiRefNet trust_remote_code needs from the repo
        needed = [
            "config.json",
            "birefnet.py",
            "BiRefNet_config.py",
            "model.safetensors",
            "handler.py",
        ]

        local_dir = self._download_with_progress(needed)

        try:
            model = AutoModelForImageSegmentation.from_pretrained(
                local_dir,
                trust_remote_code=True,
                use_safetensors=True,
                local_files_only=True,
            )
        except Exception as exc:
            msg = str(exc)
            if "connection" in msg.lower() or "timeout" in msg.lower() or "network" in msg.lower():
                kind = "download"
            else:
                kind = "model_load"
            raise EngineError(kind, f"Failed to load model: {msg}") from exc

        model.to(torch.device("cpu"))
        model.eval()
        self.model = model

    def _download_with_progress(self, needed: list[str]) -> str:
        """Download model files via snapshot_download, reporting progress.

        Returns the local snapshot directory path.
        """
        import os
        import threading
        import time as _time

        from huggingface_hub import snapshot_download, HfApi

        endpoint = os.environ.get("HF_ENDPOINT")
        api = HfApi(endpoint=endpoint)

        # Query total size of needed files
        total_bytes = 0
        try:
            info = api.model_info(self.model_id)
            for s in info.siblings:
                if s.rfilename in needed and s.size is not None:
                    total_bytes += s.size
        except Exception:
            pass  # unknown total -> progress shows downloaded only

        cache_dir = self.cache_dir
        # Determine the repo cache root to monitor for size growth
        if cache_dir:
            repo_cache_root = os.path.join(
                cache_dir,
                "models--" + self.model_id.replace("/", "--"),
            )
        else:
            from huggingface_hub.constants import HF_HUB_CACHE
            repo_cache_root = os.path.join(
                HF_HUB_CACHE,
                "models--" + self.model_id.replace("/", "--"),
            )

        stop = threading.Event()

        def _dir_size(path: str) -> int:
            total = 0
            if not os.path.isdir(path):
                return 0
            for root, _dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            return total

        def _monitor():
            last_bytes = 0
            last_time = _time.time()
            while not stop.is_set():
                cur = _dir_size(repo_cache_root)
                now = _time.time()
                dt = max(now - last_time, 0.1)
                speed = (cur - last_bytes) / dt
                if self.progress_cb:
                    self.progress_cb(cur, total_bytes, speed)
                last_bytes = cur
                last_time = now
                stop.wait(0.5)

        mon = threading.Thread(target=_monitor, daemon=True)
        mon.start()

        try:
            local_dir = snapshot_download(
                repo_id=self.model_id,
                cache_dir=self.cache_dir,
                allow_patterns=needed,
                endpoint=endpoint,
            )
        except Exception as exc:
            stop.set()
            msg = str(exc)
            if "connection" in msg.lower() or "timeout" in msg.lower() or "network" in msg.lower():
                kind = "download"
            else:
                kind = "download"
            raise EngineError(kind, f"Failed to download model: {msg}") from exc
        finally:
            stop.set()

        # Final progress report at 100%
        if self.progress_cb:
            self.progress_cb(total_bytes, total_bytes, 0.0)
        return local_dir

    def infer(self, rgb_pil: Image.Image) -> np.ndarray:
        """Run BiRefNet inference, return continuous alpha mask.

        Args:
            rgb_pil: RGB PIL image at original resolution (H×W).

        Returns:
            float32 array (H, W) in [0,1] — same H×W as input.

        Raises:
            EngineError: if model not loaded or inference fails.
        """
        if not self.is_loaded:
            raise EngineError("model_load", "Model not loaded. Call load() first.")

        from furniture_cutout.image_processing import letterbox, unletterbox_mask

        # Pad value: ImageNet mean * 255 ≈ (124, 116, 104)
        pad_value = (124, 116, 104)

        # === Letterbox: resize keeping aspect ratio, pad to square ===
        padded, scale, pad_l, pad_t = letterbox(
            rgb_pil, MODEL_INPUT_SIZE, pad_value=pad_value,
        )

        orig_w, orig_h = rgb_pil.size  # PIL size = (width, height)

        # === Preprocess: PIL → tensor → normalize ===
        # Convert to float32 CHW tensor in [0,1]
        img_np = np.array(padded, dtype=np.float32) / 255.0  # (H,W,C) uint8→float32
        # HWC → CHW
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)  # (1,3,S,S)

        # ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1)
        img_tensor = (img_tensor - mean) / std

        # Enable TF32 CPU matmul precision for modest speedup
        torch.set_float32_matmul_precision("high")

        # === Inference ===
        try:
            with torch.inference_mode():
                preds = self.model(img_tensor)
                # model returns list/tuple of predictions; take last, apply sigmoid
                logits = preds[-1]
                alpha = torch.sigmoid(logits)  # (1,1,S,S) float32 [0,1]
                alpha = alpha[0, 0]  # (S,S) float32
                alpha_np = alpha.cpu().numpy()  # (S,S) float32 [0,1]
        except Exception as exc:
            raise EngineError("inference", f"Inference failed: {exc}") from exc
        finally:
            # Free intermediate tensors
            del img_tensor
            if "preds" in locals():
                del preds
            if "logits" in locals():
                del logits
            if "alpha" in locals():
                del alpha

        # === Unletterbox: remove padding → resize back to original H×W ===
        alpha_full = unletterbox_mask(
            alpha_np, (orig_h, orig_w), scale, (pad_l, pad_t),
        )

        # === Sanitise ===
        alpha_full = np.nan_to_num(alpha_full, nan=0.0, posinf=1.0, neginf=0.0)
        np.clip(alpha_full, 0.0, 1.0, out=alpha_full)

        return alpha_full
