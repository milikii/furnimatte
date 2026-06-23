"""Exporter: save RGBA PNG with straight alpha, optional alpha mask."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


class ExporterError(Exception):
    """Export operation failed."""

    pass


def save(
    rgba_pil: Image.Image,
    src_path: str,
    out_dir: str | None = None,
    also_alpha: bool = False,
) -> str:
    """Save RGBA image as PNG with straight (non-premultiplied) alpha.

    Output filename: <src_stem>_cutout.png
    Defaults to source file directory if out_dir is None.
    Never overwrites the source file.
    Increments suffix (_1, _2, ...) on collision.

    Returns:
        Path to saved file.
    """
    if rgba_pil.mode != "RGBA":
        raise ExporterError("输入图像必须为 RGBA 模式")

    src_path = Path(src_path)
    if out_dir:
        out_base = Path(out_dir)
    else:
        out_base = src_path.parent

    out_base.mkdir(parents=True, exist_ok=True)

    stem = src_path.stem
    out_name = f"{stem}_cutout.png"
    out_path = out_base / out_name

    # Detect collision with source
    if out_path.resolve() == src_path.resolve():
        raise ExporterError("输出文件与原始文件相同，拒绝覆盖")

    # Increment on collision
    counter = 1
    while out_path.exists():
        out_name = f"{stem}_cutout_{counter}.png"
        out_path = out_base / out_name
        counter += 1

    try:
        rgba_pil.save(str(out_path), format="PNG")
    except (OSError, PermissionError) as e:
        raise ExporterError(f"保存失败：{e}") from e

    if also_alpha:
        save_alpha(alpha_from_rgba(rgba_pil), src_path, str(out_base))

    return str(out_path)


def save_alpha(
    alpha_np: np.ndarray,
    src_path: str,
    out_dir: str | None = None,
) -> str:
    """Save alpha mask as grayscale PNG.

    alpha_np: float [0,1] (H, W)
    Returns path to saved file.
    """
    src_path = Path(src_path)
    if out_dir:
        out_base = Path(out_dir)
    else:
        out_base = src_path.parent
    out_base.mkdir(parents=True, exist_ok=True)

    stem = src_path.stem
    out_name = f"{stem}_alpha.png"
    out_path = out_base / out_name

    counter = 1
    while out_path.exists():
        out_name = f"{stem}_alpha_{counter}.png"
        out_path = out_base / out_name
        counter += 1

    alpha_u8 = (np.clip(alpha_np, 0, 1) * 255).astype(np.uint8)
    try:
        Image.fromarray(alpha_u8, mode="L").save(str(out_path), format="PNG")
    except (OSError, PermissionError) as e:
        raise ExporterError(f"保存 Alpha 蒙版失败：{e}") from e

    return str(out_path)


def alpha_from_rgba(rgba_pil: Image.Image) -> np.ndarray:
    """Extract alpha channel from RGBA PIL image as float [0,1] array."""
    arr = np.array(rgba_pil, dtype=np.float32)
    return arr[:, :, 3] / 255.0
