"""BiRefNet CPU inference engine with letterbox preprocessing."""

from __future__ import annotations

import os
import time

import numpy as np
import torch
from PIL import Image

from furniture_cutout.image_processing import letterbox, unletterbox_mask

MODEL_INPUT_SIZE = 2048  # HR-matting resolution (verified from model card)

# ImageNet normalization (verified from model card)
_MEAN = (0.485, 0.456, 0.406)
_STD = (0.229, 0.224, 0.225)
_PAD_VALUE = tuple(int(round(m * 255)) for m in _MEAN)  # ~(124, 116, 104)


class EngineError(Exception):
    """BiRefNet engine error with kind classification."""

    def __init__(self, kind: str, message: str):
        self.kind = kind  # model_load | download | inference
        self.message = message
        super().__init__(message)


class BiRefNetEngine:
    """Encapsulates BiRefNet_HR-matting model loading and CPU inference.

    Model loaded once; subsequent infer() calls reuse it.
    All operations on CPU float32.
    """

    def __init__(
        self,
        model_id: str = "ZhengPeng7/BiRefNet_HR-matting",
        cache_dir: str | None = None,
        num_threads: int | None = None,
        progress_cb=None,
    ):
        self._model_id = model_id
        self._cache_dir = cache_dir
        self._num_threads = num_threads
        self._progress_cb = progress_cb
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Download (if needed) and load model onto CPU. Thread-safe for single use."""
        try:
            from transformers import AutoModelForImageSegmentation  # noqa: PLC0415
        except ImportError:
            raise EngineError("model_load", "transformers 未安装，请运行 install.bat 安装依赖")

        try:
            if self._num_threads is not None:
                torch.set_num_threads(self._num_threads)
                torch.set_num_interop_threads(1)

            torch.set_float32_matmul_precision("high")

            model = AutoModelForImageSegmentation.from_pretrained(
                self._model_id,
                trust_remote_code=True,
                cache_dir=self._cache_dir,
            )
            device = torch.device("cpu")
            model.to(device)
            model.eval()
            self._model = model
        except EnvironmentError as e:
            msg = str(e)
            if "connect" in msg.lower() or "timeout" in msg.lower() or "resolve" in msg.lower():
                raise EngineError("download", f"无法下载模型 {self._model_id}：网络错误。请检查网络、代理或设置 HF 镜像。") from e
            raise EngineError("model_load", f"模型加载失败：{e}") from e
        except Exception as e:
            raise EngineError("model_load", f"模型加载失败：{e}") from e

    def infer(self, rgb_pil: Image.Image) -> np.ndarray:
        """Run inference and return alpha mask at original image size.

        Args:
            rgb_pil: RGB PIL image at original size

        Returns:
            float32 numpy array [0,1] with shape (H, W) == original image size
        """
        if self._model is None:
            raise EngineError("inference", "模型未加载，请先调用 load()")

        orig_hw = (rgb_pil.height, rgb_pil.width)

        try:
            # 1. Letterbox preprocessing
            padded, scale, pad_l, pad_t = letterbox(rgb_pil, MODEL_INPUT_SIZE, _PAD_VALUE)

            # 2. To tensor + normalize
            img_np = np.array(padded, dtype=np.float32) / 255.0
            img_np = (img_np - _MEAN) / _STD  # (H, W, 3)
            img_t = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)  # (1,3,S,S)

            # 3. Inference (float32, CPU, no_grad)
            with torch.inference_mode():
                # Move model to eval if not already (already in load())
                preds = self._model(img_t)
                # Model output: list/tuple of predictions, last element is the final mask
                if isinstance(preds, (list, tuple)):
                    logits = preds[-1]
                else:
                    logits = preds
                alpha = torch.sigmoid(logits)  # (1,1,S,S) in [0,1]

            # 4. Extract single channel
            alpha_np = alpha[0, 0].cpu().numpy()  # (S, S)

            # 5. Unletterbox: remove padding, resize to original
            alpha_full = unletterbox_mask(alpha_np, orig_hw, scale, (pad_l, pad_t))

            # 6. Defensive cleaning
            alpha_full = np.nan_to_num(alpha_full, nan=0.0, posinf=1.0, neginf=0.0)
            alpha_full = np.clip(alpha_full, 0.0, 1.0)

            # Clean up intermediate tensors
            del img_t, alpha, alpha_np

            return alpha_full

        except EngineError:
            raise
        except Exception as e:
            raise EngineError("inference", f"推理失败：{e}") from e
