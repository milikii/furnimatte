"""Image processing utilities: load, letterbox, alpha mapping, RGBA composite."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image, ImageOps
from PySide6.QtGui import QImage


def load_image(path: str) -> tuple[Image.Image, dict]:
    """Open image, apply EXIF orientation, convert to RGB.

    Returns:
        (rgb_pil, meta_dict) where meta = {"width": w, "height": h, "path": path}
    """
    im = Image.open(path)
    im = ImageOps.exif_transpose(im) or im
    im = im.convert("RGB")
    meta = {"width": im.width, "height": im.height, "path": path}
    return im, meta


def make_preview(rgb_pil: Image.Image, max_side: int = 1024) -> Image.Image:
    """Scale down keeping aspect ratio so longest side ≤ max_side. Never upscale."""
    w, h = rgb_pil.size
    if max(w, h) <= max_side:
        return rgb_pil.copy()
    scale = max_side / max(w, h)
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    return rgb_pil.resize((new_w, new_h), Image.BILINEAR)


def letterbox(
    img_pil: Image.Image, target: int = 1024, pad_value: tuple[int, int, int] = (114, 114, 114)
) -> tuple[Image.Image, float, int, int]:
    """Resize keeping aspect ratio so longest side = target, pad short side to square.

    Returns:
        (padded_pil, scale, pad_left, pad_top)
        scale = target / original_longest_side
        pad_left, pad_top = padding dimensions applied (pixels in padded image space)
    """
    w, h = img_pil.size
    scale = target / max(w, h)
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    resized = img_pil.resize((new_w, new_h), Image.BILINEAR)

    pad_w = target - new_w
    pad_h = target - new_h
    pad_left = pad_w // 2
    pad_top = pad_h // 2

    padded = Image.new("RGB", (target, target), color=pad_value)
    padded.paste(resized, (pad_left, pad_top))
    return padded, scale, pad_left, pad_top


def unletterbox_mask(
    mask_np: np.ndarray,
    orig_hw: tuple[int, int],
    scale: float,
    pad_lt: tuple[int, int],
) -> np.ndarray:
    """Remove letterbox padding from mask and resize to original dimensions.

    Args:
        mask_np: float array (H, W) in [0,1] from model output (may be square)
        orig_hw: (orig_H, orig_W)
        scale: scale factor used in letterbox
        pad_lt: (pad_left, pad_top) used in letterbox

    Returns:
        float array (orig_H, orig_W) in [0,1]
    """
    pad_l, pad_t = pad_lt
    new_w = max(1, round(orig_hw[1] * scale))
    new_h = max(1, round(orig_hw[0] * scale))

    # Crop out padding
    cropped = mask_np[pad_t : pad_t + new_h, pad_l : pad_l + new_w]

    # Resize to original dimensions
    if (cropped.shape[0], cropped.shape[1]) != orig_hw:
        cropped = cv2.resize(cropped, (orig_hw[1], orig_hw[0]), interpolation=cv2.INTER_LINEAR)
    return cropped


def expand_box(
    box: tuple[int, int, int, int],
    pad_ratio: float,
    img_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Expand box by pad_ratio of longer side, clamped to image bounds.

    Args:
        box: (x, y, w, h) in image coordinates
        pad_ratio: fraction of longer side to expand (e.g. 0.05)
        img_size: (img_w, img_h)

    Returns:
        (x, y, w, h) expanded box
    """
    x, y, w, h = box
    pad = int(max(w, h) * pad_ratio)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(img_size[0], x + w + pad)
    y2 = min(img_size[1], y + h + pad)
    return (x1, y1, x2 - x1, y2 - y1)


def crop_roi(rgb_pil: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Crop region of interest from image.

    Args:
        rgb_pil: source RGB PIL image
        box: (x, y, w, h)

    Returns:
        ROI PIL Image
    """
    x, y, w, h = box
    return rgb_pil.crop((x, y, x + w, y + h))


def map_roi_alpha_to_full(
    roi_alpha: np.ndarray,
    box: tuple[int, int, int, int],
    img_size: tuple[int, int],
) -> np.ndarray:
    """Place ROI alpha at the correct position in a full-size zeroed alpha.

    If ROI alpha dimensions don't match box (e.g. due to 1px rounding),
    resize to match.

    Args:
        roi_alpha: float [0,1] (roi_H, roi_W)
        box: (x, y, w, h) where the ROI sits in the full image
        img_size: (img_w, img_h)

    Returns:
        float [0,1] (img_h, img_w)
    """
    x, y, w, h = box
    full = np.zeros((img_size[1], img_size[0]), dtype=np.float32)
    # Resize roi_alpha to box dimensions if needed
    if roi_alpha.shape != (h, w):
        roi_alpha = cv2.resize(roi_alpha, (w, h), interpolation=cv2.INTER_LINEAR)
    full[y : y + h, x : x + w] = roi_alpha
    return full


def compose_rgba(rgb_pil: Image.Image, alpha_np: np.ndarray) -> Image.Image:
    """Compose RGB + alpha into RGBA (straight alpha, non-premultiplied).

    Transparent pixels (alpha == 0) have RGB zeroed.
    Semi-transparent pixels keep original RGB (straight alpha).

    Args:
        rgb_pil: RGB PIL image (original size)
        alpha_np: float [0,1] (H, W) matching rgb_pil size

    Returns:
        RGBA PIL image (same size as input)
    """
    # Defensive cleaning
    alpha = np.nan_to_num(alpha_np, nan=0.0, posinf=1.0, neginf=0.0)
    alpha = np.clip(alpha, 0.0, 1.0)

    rgb = np.array(rgb_pil, dtype=np.uint8)  # (H, W, 3)
    h, w = rgb.shape[:2]

    if alpha.shape != (h, w):
        alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_LINEAR)

    alpha_u8 = (alpha * 255).astype(np.uint8)

    # Straight (non-premultiplied) alpha: for fully transparent pixels, zero RGB
    mask = alpha_u8 == 0
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = alpha_u8
    # Zero RGB where alpha is fully transparent (optional but spec says)
    rgba[mask, 0] = 0
    rgba[mask, 1] = 0
    rgba[mask, 2] = 0

    return Image.fromarray(rgba, mode="RGBA")


def qimage_from_pil(pil_img: Image.Image) -> QImage:
    """Convert PIL Image to QImage."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    data = buf.read()
    qimg = QImage.fromData(data)
    return qimg


def checkerboard(w: int, h: int, cell: int = 16) -> QImage:
    """Generate checkerboard background QImage using numpy for speed."""
    # Cell-level pattern
    cw = max(1, (w + cell - 1) // cell)
    ch = max(1, (h + cell - 1) // cell)
    pattern = np.fromfunction(
        lambda i, j: ((i + j) % 2 == 0).astype(np.uint8),
        (ch, cw),
    )
    # Expand cells to pixels
    full = np.kron(pattern, np.ones((cell, cell), dtype=np.uint8))
    full = full[:h, :w]
    # Convert to RGB: 255=white, 128=gray
    gray = np.where(full, 255, 128).astype(np.uint8)
    rgb = np.stack([gray, gray, gray], axis=-1)
    pil = Image.fromarray(rgb, mode="RGB")
    return qimage_from_pil(pil)
