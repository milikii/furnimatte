【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §8、§9、`dispatch/T03..T06`（被测模块契约）是依据。动手前读：`项目架构.md` §8 测试架构、§9 不变量、`furniture_cutout/image_processing.py`、`furniture_cutout/exporter.py`（已存在，读其真实签名）。前置 T03、T04（T05 完成后冒烟测试才可跑，但默认 skip）。本任务 **T13 测试**。

【范围 + 文件白名单】仅建：`tests/test_image_mapping.py`, `tests/test_box_coordinates.py`, `tests/test_export_size.py`, `tests/test_alpha_composite.py`, `tests/test_engine_smoke.py`, `conftest.py`。不改其它文件。

【任务】实现 4 个逻辑单测（无需模型，必须全绿）+ 1 个冒烟（默认 skip）+ conftest：
1. `conftest.py`：
   - 注册 marker：`pytest.ini` 在 pyproject.toml 已配；conftest 加 `def pytest_configure(config): config.addinivalue_line("markers","model: needs BiRefNet model (skipped without FURNIMATTE_MODEL=1)")`。
   - 自动 skip model 标记用例：`def pytest_collection_modifyitems(config,items): if os.environ.get("FURNIMATTE_MODEL")!="1": skip=pytest.mark.skip(reason="set FURNIMATTE_MODEL=1 to run model smoke test"); [skip.apply(item) for item in items if "model" in item.keywords]`。
2. `tests/test_image_mapping.py`：
   - test letterbox→unletterbox 往返：原图 (640,480) → letterbox(1024) → 构造已知 mask（中心 1，边缘 0）→ unletterbox 回 (480,640) → 形状==原图且中心区为 1。
   - test letterbox 保持长宽比不拉伸：padded 是正方形，有效区比例==原图。
   - test unletterbox 尺寸==原图（§9 不变量 1 的前提）。
3. `tests/test_box_coordinates.py`：
   - test expand_box：box=(100,100,50,50), ratio=0.1, img=(640,480) → 扩展且不越界（x≥0,y≥0,x+w≤640,y+h≤480）。
   - test expand_box clamp 边界：box=(600,400,50,50), ratio=0.2, img=(640,480) → 不越界。
   - test map_roi_alpha_to_full：roi_alpha 全 1 (50,50), box=(100,100,50,50), img=(640,480) → 仅 box 区为 1，框外全 0。
   - test 小框语义：assert expand_box((10,10,30,30),...) 仍可算，但 50px 判定由 main_window——本测试只验几何（可选）。
4. `tests/test_export_size.py`：
   - test 输出 PNG 尺寸==原图（§9 不变量 1）：建 (200,150) RGBA → save → open → assert size==(200,150) and mode=='RGBA'。
   - test 不覆盖原图：src=a.jpg，cutout=a_cutout.png，assert out_path != src_path。
   - test 重名加序号：第二次 save → a_cutout_1.png。
   - test Straight alpha：设半透明像素 alpha=128，保存后读回 RGBA，assert RGB 未被预乘（R 值保持原值）。
5. `tests/test_alpha_composite.py`：
   - test compose_rgba 输出 RGBA 且尺寸==原图。
   - test 透明区 RGB=0：alpha=0 处 RGB==0。
   - test 半透明边缘保留原 RGB：alpha=0.5 处 RGB==原图 RGB（非预乘）。
   - test alpha 不二值化：输入 alpha=0.3 → 输出 alpha 通道==round(0.3*255)=76（非 0/255）。
6. `tests/test_engine_smoke.py`（`@pytest.mark.model`）：
   - 需要 FURNIMATTE_MODEL=1 且模型已下载。建合成图（中央白块）→ BiRefNetEngine().load() → infer() → assert 输出 shape==输入 H×W 且 dtype float 且值域 [0,1] 且非全相同（有梯度）。
   - 第二次 infer 不重建模型（简单 assert is_loaded 仍 True）。

【决策规则】
- 测试只 import furniture_cutout 内模块 + PIL/numpy/pytest。不 import torch（除冒烟）。
- 测试用合成小图（PIL.Image.new），不依赖外部素材。
- 不修改被测源码；若发现源码 bug，**停下报告**，不要改源码（越界）。
- 冒烟测试默认 skip，仅 FURNIMATTE_MODEL=1 时跑。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `pytest -q` 全绿（4 逻辑单测 pass；engine_smoke skipped）
- `ruff check tests/` 退出 0
- grep 自检：`grep -rnE "type: ignore|except\s*:\s*pass" tests/` 为空
- `pytest -q --co` 列出至少 4 个 test_image_mapping/test_box/test_export/test_alpha 的用例 + 1 个 model 用例
- `git status`：仅白名单 6 个文件

【铁律】发现源码 bug 停下报告，不改源码。需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】每个文件改了什么 + `pytest -q` 实际输出（pass/skip 计数）+ 每条门槛结果。
