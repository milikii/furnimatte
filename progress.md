# Progress

## Status
T05 — BiRefNet Engine (In Review)

## Tasks
- T05: furniture_cutout/birefnet_engine.py implemented
  - MODEL_INPUT_SIZE=2048 (HR-matting official)
  - Letterbox preprocessing (spec-authorised deviation from official stretch-resize)
  - ImageNet normalization [0.485,0.456,0.406]/[0.229,0.224,0.225]
  - model(input)[-1].sigmoid() output parsing
  - Float32 CPU, no fp16/cuda, torch.set_float32_matmul_precision('high')
  - Continuous [0,1] alpha, no binarisation
  - EngineError with kind classification

## Files Changed
- furniture_cutout/birefnet_engine.py (new, 5700 bytes)

## Notes
- Acceptance criteria all satisfied
- Model smoke test deferred to T13 (requires download)
