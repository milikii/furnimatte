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

        try:
            model = AutoModelForImageSegmentation.from_pretrained(
                self.model_id,
                trust_remote_code=True,
                cache_dir=self.cache_dir,
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
