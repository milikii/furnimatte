【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.1、§4、§5 是契约（**最关键模块，多任务依赖**）。动手前**完整读**：`项目架构.md` §2.1 函数表、§4 坐标系、§5 预处理管线、§9 不变量。前置 T01 已完成。本任务 **T03 图像处理**。

【范围 + 文件白名单】仅建 `furniture_cutout/image_processing.py`。不改其它文件。

【任务】实现 `furniture_cutout/image_processing.py`，函数签名与契约**严格**按 §2.1：
1. `load_image(path: str) -> tuple[PIL.Image.Image, dict]`：`ImageOps.exif_transpose` 应用 EXIF；转 RGB；返回 (rgb_pil, {"width":w,"height":h,"path":path})。保留原始尺寸。
2. `make_preview(rgb_pil, max_side=1024) -> PIL.Image`：等比缩放，长边≤max_side，不放大（原图更小则原样返回）。
3. `letterbox(img_pil, target=1024, pad_value=(114,114,114)) -> tuple[PIL.Image.Image, float, int, int]`：长边→target 等比缩放（保持比例，**不拉伸**）；短边两侧 pad 到正方形；返回 (padded, scale=缩放比例, pad_left, pad_top)。
4. `unletterbox_mask(mask_np: np.ndarray, orig_hw: tuple[int,int], scale: float, pad_lt: tuple[int,int]) -> np.ndarray`：mask_np 形状 (h,h) 或 (h,w) float；先裁掉 padding（用 pad_lt 反算 padded 内的有效区），再 `cv2.resize` 到 orig_hw（INTER_LINEAR），返回 float [0,1] (H×W)。
5. `expand_box(box: tuple[int,int,int,int], pad_ratio: float, img_size: tuple[int,int]) -> tuple[int,int,int,int]`：box=(x,y,w,h)；pad = max(w,h)*pad_ratio；四向扩展；clamp 到 [0,img_w]/[0,img_h]；返回 (x,y,w,h)（扩展后）。
6. `crop_roi(rgb_pil, box) -> PIL.Image`：`rgb_pil.crop((x,y,x+w,y+h))`。
7. `map_roi_alpha_to_full(roi_alpha: np.ndarray, box: tuple[int,int,int,int], img_size: tuple[int,int]) -> np.ndarray`：建全 0 (H×W) float；将 roi_alpha（尺寸应==box w×h）贴到 box 区域；框外保持 0。若 roi_alpha 尺寸与 box 不符，用 `cv2.resize` 适配（防 1px 误差）。
8. `compose_rgba(rgb_pil, alpha_np) -> PIL.Image.Image`：rgb_pil 转 RGB（原图尺寸）；alpha_np float [0,1] (H×W) → uint8；建 RGBA：透明区(alpha==0) RGB=0，半透明边缘保留**原 RGB**；输出尺寸==原图；**Straight（非预乘）Alpha**。
9. `qimage_from_pil(pil_img) -> QImage`：PIL → QByteArray → QImage（Format_RGBA8888 或 RGB888）。
10. `checkerboard(w, h, cell=16) -> QImage`：生成棋盘格背景 QImage。

【决策规则（遇到就照此，不要自创）】
- 归一化/推理不归本模块管（engine 管）；本模块只做几何与合成。
- `cv2.resize` 一律 `INTER_LINEAR`（升采样 Alpha 用，避免 CUBIC 过冲）。
- Alpha 不得二值化；不得腐蚀/膨胀/羽化/锐化/填孔/删小区域。
- 原始 RGB 不得被修改；合成时取原图 RGB。
- `np.nan_to_num` + `np.clip(0,1)` 在 compose 前对 alpha 做一次（防御）。
- `expand_box` 的 pad_ratio 来自设置（0/0.05/0.10/0.15），本函数不读设置，由调用方传。
- 类型用 `from __future__ import annotations` 或直接字符串注解；不引入 mypy 强制。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import image_processing as ip; print([f for f in dir(ip) if not f.startswith('_')])"` 列出全部 10 个函数
- `python -c "from furniture_cutout import image_processing as ip; from PIL import Image; import numpy as np; im=Image.new('RGB',(640,480)); a=np.zeros((480,640),dtype=np.float32); r=ip.compose_rgba(im,a); assert r.size==(640,480) and r.mode=='RGBA'"` 成功
- `python -c "from furniture_cutout import image_processing as ip; from PIL import Image; im=Image.new('RGB',(640,480)); p,s,pl,pt=ip.letterbox(im,1024); assert p.size==(1024,1024) and abs(s-1024/640)<1e-6"` 成功
- `python -c "from furniture_cutout import image_processing as ip; print(ip.expand_box((100,100,50,50),0.1,(640,480)))"` 不越界
- `ruff check furniture_cutout/image_processing.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*(Exception|BaseException)?\s*:\s*pass|except\s*:\s*pass|> 0\.5|alpha\s*>\s*0|threshold" furniture_cutout/image_processing.py` 为空（不得二值化/阈值）
- `git status`：仅 `furniture_cutout/image_processing.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。禁止改原始 RGB。禁止 Alpha 二值化。

【报告格式】文件改了什么 + 每条门槛实际输出/结论。
