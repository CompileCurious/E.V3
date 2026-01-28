"""
Lightweight Mistral loader wrapper.
Attempts to load quantized/bitsandbytes model when GPU available,
otherwise falls back to CPU-friendly load with memory-safety flags.

Provides `MistralLLM` with `generate(prompt, max_tokens)` and `chat(messages, max_tokens)`.
"""
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
except Exception as e:
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    logger.debug(f"Transformers/torch not available: {e}")


class MistralLLM:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.tokenizer = None
        self.model = None
        self.device = None
        self.ready = False
        self._load_model()

    def _load_model(self):
        if AutoTokenizer is None or AutoModelForCausalLM is None or torch is None:
            logger.error("Required packages not installed: transformers and torch")
            return

        model_id = self.config.get("model_id") or self.config.get("model") or "mistral-7b"
        model_path = self.config.get("model_path") or self.config.get("model_dir") or "models/llm"
        repo_or_path = model_id
        # If a directory exists combining path+id, prefer that
        candidate = os.path.join(model_path, model_id)
        if os.path.exists(candidate):
            repo_or_path = candidate

        logger.info(f"Loading Mistral model from: {repo_or_path}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(repo_or_path, use_fast=True)

            use_cuda = torch.cuda.is_available()
            self.device = torch.device("cuda") if use_cuda else torch.device("cpu")

            # Try to load with bitsandbytes 8-bit quant if GPU available
            if use_cuda:
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        repo_or_path,
                        device_map="auto",
                        load_in_8bit=True,
                        torch_dtype=torch.float16,
                    )
                    logger.info("Loaded model in 8-bit on GPU via bitsandbytes")
                except Exception as be:
                    logger.warning(f"Bitsandbytes load failed, falling back to fp16/device_map auto: {be}")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        repo_or_path,
                        device_map="auto",
                        torch_dtype=torch.float16,
                    )
            else:
                # CPU path: load with low_cpu_mem_usage and map to CPU
                self.model = AutoModelForCausalLM.from_pretrained(
                    repo_or_path,
                    device_map={"": "cpu"},
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                )

            self.model.eval()
            self.ready = True
            logger.info("Mistral model loaded and ready")

        except Exception as e:
            logger.error(f"Failed to load Mistral model: {e}")
            self.ready = False

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        formatted = "<s>"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted += f"{content}\n\n"
            elif role == "user":
                formatted += f"[INST] {content} [/INST]"
            elif role == "assistant":
                formatted += f"{content}</s>"
        return formatted

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> str:
        if not self.ready:
            return "Local Mistral model not available."

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"]
            attention_mask = inputs.get("attention_mask")

            # Move tensors to model device
            try:
                input_ids = input_ids.to(next(self.model.parameters()).device)
                if attention_mask is not None:
                    attention_mask = attention_mask.to(next(self.model.parameters()).device)
            except Exception:
                pass

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,
                    do_sample=(temperature > 0.0),
                    temperature=temperature,
                    top_p=0.95,
                    eos_token_id=getattr(self.tokenizer, "eos_token_id", None),
                )

            # Strip prompt tokens from output
            generated = outputs[0]
            # If returned as tensor of full sequence, decode from input length
            try:
                decoded = self.tokenizer.decode(generated[input_ids.shape[-1]:], skip_special_tokens=True)
            except Exception:
                decoded = self.tokenizer.decode(generated, skip_special_tokens=True)

            return decoded.strip()

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return "Error running model."

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256, temperature: float = 0.7) -> str:
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, max_tokens=max_tokens, temperature=temperature)
