"""
Helper to download Mistral model files into `models/llm/<model-id>` using `huggingface_hub`.
Usage:
  - Set `HF_TOKEN` env var if the model is private.
  - Run: `python tools/download_mistral.py --model-id <model-id>`

This script is intentionally minimal: it uses `huggingface_hub.snapshot_download` when available.
"""
import os
import argparse
import sys

try:
    from huggingface_hub import snapshot_download
except Exception:
    snapshot_download = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True, help="Hugging Face model id (or local folder)")
    parser.add_argument("--output-dir", default="models/llm", help="Base output dir")
    args = parser.parse_args()

    model_id = args.model_id
    out_base = args.output_dir
    target = os.path.join(out_base, model_id)

    if os.path.exists(target) and os.listdir(target):
        print(f"Target {target} already exists and is not empty. Skipping download.")
        return

    if snapshot_download is None:
        print("huggingface_hub not available. Install it with: pip install huggingface-hub")
        sys.exit(1)

    hf_token = os.getenv("HF_TOKEN")
    print(f"Downloading {model_id} to {target} (token provided: {'yes' if hf_token else 'no'})")
    try:
        snapshot_download(repo_id=model_id, cache_dir=out_base, local_dir=target, token=hf_token)
        print("Download complete.")
    except Exception as e:
        print("Download failed:", e)
        raise


if __name__ == '__main__':
    main()
