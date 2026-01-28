"""Quick test harness for Mistral loader.
This script attempts to instantiate the MistralLLM and run a small generate.
It prints diagnostics so we can see whether transformers/torch are available and whether a model was found.
"""
import traceback

from pprint import pprint

try:
    from service.llm.mistral_loader import MistralLLM
except Exception as e:
    print("Failed to import MistralLLM:", e)
    traceback.print_exc()
    raise

cfg = {
    "model_id": "mistral-7b",
    "model_path": "models/llm",
    # additional flags can go here
}

try:
    m = MistralLLM(cfg)
    print("MistralLLM ready:", m.ready)
    print("Device:", getattr(m, 'device', None))
    print("Tokenizer loaded:", bool(getattr(m, 'tokenizer', None)))

    # Run a short generate to ensure pipeline runs (may return 'not available' if model missing)
    out = m.generate("Hello, what's your name?", max_tokens=16)
    print("Generate result:\n", out)

except Exception as e:
    print("Error while testing MistralLLM:", e)
    traceback.print_exc()
    raise
