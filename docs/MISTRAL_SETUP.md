# Mistral Model Setup

This document explains how to obtain and place a Mistral model for local use by E.V3.

Recommended layout:

- Put model files under `models/llm/<model-id>` (e.g. `models/llm/mistral-7b`).
- The `service.llm.mistral_loader` will look for `llm.local.model_id` and `llm.local.model_path` in the config.

Options to obtain models:

1. Hugging Face Model Hub (recommended)
   - If the model is public, you can `git lfs` clone or use `huggingface_hub` to download files.
   - If model is in a private repo, login with `huggingface-cli login` and ensure your token has access.

2. Manual download
   - Download the model weights from the provider and place them under `models/llm/<model-id>`.

CPU vs GPU:

- The loader will attempt to use GPU with bitsandbytes when `torch.cuda.is_available()`.
- On CPU-only machines the loader will use `low_cpu_mem_usage=True` when loading via `transformers`.
- For best performance on CPU, use a quantized model compatible with `transformers` or use GGUF via a different backend (llama-cpp).

Example config snippet (`config/config.yaml`):

```yaml
llm:
  local:
    enabled: true
    engine: mistral
    model_id: mistral-7b
    model_path: models/llm
    # Optional: model_dir, context_length, temperature, etc.
```

Troubleshooting:

- If you see errors about `model not found` or `not a local folder`, confirm `models/llm/<model-id>` exists and contains the model files.
- If you need to authenticate to Hugging Face, run `huggingface-cli login` in your shell and provide a token.

See `tools/download_mistral.py` for an automated helper that can use `huggingface_hub`.
