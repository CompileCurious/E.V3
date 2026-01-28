"""
LLM Integration for E.V3
Local Mistral 7B for privacy, optional GPT mini for external queries
Privacy: Strict controls to prevent data leakage
"""

from typing import Optional, Dict, Any, List
from loguru import logger
import os
from abc import ABC, abstractmethod


class LLMBase(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256) -> str:
        """Generate chat response"""
        pass


class LocalLLM(LLMBase):
    """
    Local Mistral 7B using llama.cpp
    Privacy: All processing happens locally, no external calls
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the local LLM model"""
        try:
            from llama_cpp import Llama
            
            model_path = self.config.get("model_path", "models/llm/")
            model_file = self.config.get("model", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
            full_path = os.path.join(model_path, model_file)
            
            if not os.path.exists(full_path):
                logger.warning(f"Model file not found: {full_path}")
                logger.info("Please download the model from: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
                return
            
            # Initialize model
            n_gpu_layers = self.config.get("gpu_layers", 35) if self.config.get("use_gpu", True) else 0
            
            self.model = Llama(
                model_path=full_path,
                n_ctx=self.config.get("context_length", 4096),
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            logger.info("Local LLM initialized successfully")
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        except Exception as e:
            logger.error(f"Failed to initialize local LLM: {e}")
    
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """
        Generate response from prompt
        Privacy: No data leaves the machine
        """
        if not self.model:
            return "Local LLM not available."
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=self.config.get("temperature", 0.7),
                stop=["</s>", "[/INST]"],
                echo=False
            )
            
            return response["choices"][0]["text"].strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Error processing request."
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256) -> str:
        """
        Generate chat response
        Privacy: All processing local
        """
        if not self.model:
            return "Local LLM not available."
        
        try:
            # Format messages for Mistral Instruct format
            prompt = self._format_chat_prompt(messages)
            return self.generate(prompt, max_tokens)
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "Error processing chat."
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Mistral Instruct format"""
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


class ExternalLLM(LLMBase):
    """
    External LLM (GPT mini) via OpenAI API
    Privacy: Only used when explicitly requested, minimal data sent
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.enabled = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            
            api_key_env = self.config.get("api_key_env", "OPENAI_API_KEY")
            api_key = os.getenv(api_key_env)
            
            if not api_key:
                logger.warning(f"OpenAI API key not found in environment variable: {api_key_env}")
                return
            
            self.client = OpenAI(api_key=api_key)
            logger.info("External LLM client initialized")
            
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize external LLM: {e}")
    
    def enable(self):
        """Enable external LLM (user explicitly requested)"""
        self.enabled = True
        logger.info("External LLM enabled for this query")
    
    def disable(self):
        """Disable external LLM"""
        self.enabled = False
        logger.info("External LLM disabled")
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Generate response using external API
        Privacy: Only called when user says "find out"
        """
        if not self.enabled:
            logger.warning("External LLM called but not enabled")
            return "External LLM not available. Say 'find out' to enable."
        
        if not self.client:
            return "External LLM not configured."
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.config.get("temperature", 0.7)
            )
            
            # Disable after use (single-shot)
            self.disable()
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error with external LLM: {e}")
            self.disable()
            return "Error contacting external service."
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        """
        Chat with external API
        Privacy: Minimal context sent
        """
        if not self.enabled:
            return "External LLM not available. Say 'find out' to enable."
        
        if not self.client:
            return "External LLM not configured."
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.config.get("temperature", 0.7)
            )
            
            self.disable()
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error with external LLM: {e}")
            self.disable()
            return "Error contacting external service."


class LLMManager:
    """
    Manages LLM interactions with privacy controls
    Privacy: Default to local, external only on explicit trigger
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize local LLM
        self.local_llm: Optional[LocalLLM] = None
        if config.get("llm", {}).get("local", {}).get("enabled", True):
            self.local_llm = LocalLLM(config.get("llm", {}).get("local", {}))
        
        # Initialize external LLM
        self.external_llm: Optional[ExternalLLM] = None
        if config.get("llm", {}).get("external", {}).get("allow_external_on_request", True):
            self.external_llm = ExternalLLM(config.get("llm", {}).get("external", {}))
        
        # Trigger phrase for external LLM
        self.trigger_phrase = config.get("llm", {}).get("external", {}).get("trigger_phrase", "find out")
        
        # System prompt for companion personality
        self.system_prompt = """You are E.V3, a helpful and friendly desktop companion. 
You help interpret system events, provide reminders, and engage in brief small talk.
You respect user privacy and process everything locally by default.
Keep responses concise (1-2 sentences) unless more detail is needed."""
        
        logger.info("LLM Manager initialized")
    
    def process_query(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Process user query with privacy controls
        Privacy: Check for external trigger, otherwise use local
        """
        # Check if user wants to use external LLM
        if self.trigger_phrase.lower() in user_input.lower():
            logger.info("External LLM trigger detected")
            if self.external_llm:
                self.external_llm.enable()
                # Remove trigger phrase from input
                clean_input = user_input.lower().replace(self.trigger_phrase.lower(), "").strip()
                return self._query_external(clean_input, context)
            else:
                return "External LLM not configured."
        
        # Use local LLM
        return self._query_local(user_input, context)
    
    def _query_local(self, user_input: str, context: Optional[str] = None) -> str:
        """Query local LLM"""
        if not self.local_llm:
            return "Local LLM not available."
        
        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": user_input})
        
        return self.local_llm.chat(messages)
    
    def _query_external(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Query external LLM
        Privacy: Minimal context, anonymized if needed
        """
        if not self.external_llm:
            return "External LLM not available."
        
        # Build messages with minimal context
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Only send anonymized context if provided
        if context:
            anonymized_context = self._anonymize_context(context)
            messages.append({"role": "system", "content": f"Context: {anonymized_context}"})
        
        messages.append({"role": "user", "content": user_input})
        
        return self.external_llm.chat(messages)
    
    def _anonymize_context(self, context: str) -> str:
        """
        Anonymize context before sending externally
        Privacy: Remove personal information
        """
        # Simple anonymization - in production, use more sophisticated methods
        # Remove common PII patterns
        import re
        
        # Remove paths
        context = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', context)
        context = re.sub(r'/[^\s]+', '[PATH]', context)
        
        # Remove IPs
        context = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', context)
        
        # Remove emails
        context = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', context)
        
        return context
    
    def interpret_event(self, event_data: Dict[str, Any]) -> str:
        """
        Interpret system event using local LLM
        Privacy: Always use local LLM for system events
        """
        # Fallback friendly messages when LLM not available
        if not self.local_llm or not self.local_llm.model:
            source = event_data.get('source', 'System')
            event_id = event_data.get('event_id', '')
            category = event_data.get('category', 'event')
            
            # Generate friendly message based on common event patterns
            if 'defender' in source.lower() or 'antimalware' in source.lower():
                if event_id in [1116, 1117]:
                    return "✓ Virus scan complete — all good!"
                elif event_id in [5001, 5012]:
                    return "⚠️ Security alert detected. Check details for more info."
                else:
                    return f"Windows Defender event (ID: {event_id})"
            elif 'firewall' in source.lower():
                return f"Firewall activity detected (ID: {event_id})"
            else:
                return f"System {category} detected"
        
        # Create prompt for event interpretation
        prompt = f"""Interpret this system event in a friendly, concise way (1 sentence):
Event Type: {event_data.get('source', 'System')}
Event ID: {event_data.get('event_id', 'Unknown')}
Category: {event_data.get('category', 'General')}

Provide a brief, user-friendly explanation."""
        
        return self.local_llm.generate(prompt, max_tokens=128)
