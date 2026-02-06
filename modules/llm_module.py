"""
DEPRECATED: LLM Module

⚠️ This module uses the old Python-based LLM system.
For best performance, integrate with the C++ kernel instead (see kernel_cpp/docs/INTEGRATION.md).

The C++ kernel provides:
- 2-3x faster inference
- Direct llama.cpp integration
- Persistent model loading
- Native async/streaming

Legacy: Provides local and external LLM capabilities
"""

from typing import Dict, Any, Set, Optional
from loguru import logger

from kernel.module import Module, Permission, KernelAPI
from service.llm.llm_manager import LocalLLM, ExternalLLM


class LLMModule(Module):
    """
    LLM capability module
    Provides local Mistral and optional external GPT processing
    """
    
    def __init__(self, kernel_api: KernelAPI):
        super().__init__("llm", kernel_api)
        self.local_llm: Optional[LocalLLM] = None
        self.external_llm: Optional[ExternalLLM] = None
    
    def get_required_permissions(self) -> Set[Permission]:
        """LLM module needs LLM access and event handling"""
        return {
            Permission.LLM_LOCAL,
            Permission.LLM_EXTERNAL,
            Permission.EVENT_EMIT,
            Permission.EVENT_SUBSCRIBE,
            Permission.STORAGE_READ,
        }
    
    def get_dependencies(self) -> Set[str]:
        """Depends on state module for triggering alerts"""
        return {"state"}
    
    def load(self, config: Dict[str, Any]) -> bool:
        """Initialize LLM providers"""
        try:
            self.config = config
            llm_config = config.get("llm", {})
            
            # Initialize local LLM
            local_config = llm_config.get("local", {})
            if local_config.get("enabled", True):
                self.local_llm = LocalLLM(local_config)
                logger.debug("Local LLM initialized")
            
            # Initialize external LLM (disabled by default)
            external_config = llm_config.get("external", {})
            if external_config.get("enabled", False):
                self.external_llm = ExternalLLM(external_config)
                logger.debug("External LLM initialized")
            
            logger.info("LLM module loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LLM module: {e}")
            return False
    
    def enable(self) -> bool:
        """Start LLM operations"""
        try:
            # Subscribe to system events for interpretation
            self.kernel.subscribe_event(self.name, "system.defender")
            self.kernel.subscribe_event(self.name, "system.firewall")
            self.kernel.subscribe_event(self.name, "ipc.user_message")
            
            logger.info("LLM module enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable LLM module: {e}")
            return False
    
    def disable(self) -> bool:
        """Pause LLM operations"""
        logger.info("LLM module disabled")
        return True
    
    def shutdown(self) -> bool:
        """Cleanup LLM resources"""
        self.local_llm = None
        self.external_llm = None
        logger.info("LLM module shutdown")
        return True
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle events requiring LLM interpretation"""
        try:
            if event_type == "system.defender":
                self._interpret_defender_event(event_data)
                
            elif event_type == "system.firewall":
                self._interpret_firewall_event(event_data)
                
            elif event_type == "ipc.user_message":
                self._process_user_query(event_data)
                
        except Exception as e:
            logger.error(f"Error handling LLM event '{event_type}': {e}")
    
    def _interpret_defender_event(self, event_data: Dict[str, Any]):
        """Interpret Windows Defender event"""
        if not self.local_llm:
            return
        
        # Create interpretation prompt
        event_id = event_data.get("event_id", "unknown")
        threat_detected = event_data.get("threat_detected", False)
        
        prompt = f"[INST] Briefly explain this Windows Defender event (ID: {event_id}, threat: {threat_detected}) in simple terms. [/INST]"
        
        interpretation = self.local_llm.generate(prompt, max_tokens=100)
        
        # Determine priority
        priority = 2 if threat_detected else 1
        
        # Request state transition to alert
        self.kernel.emit_event(self.name, "state.transition.alert", {
            "message": interpretation,
            "priority": priority,
            "metadata": event_data
        })
    
    def _interpret_firewall_event(self, event_data: Dict[str, Any]):
        """Interpret firewall event"""
        if not self.local_llm:
            return
        
        event_id = event_data.get("event_id", "unknown")
        
        prompt = f"[INST] Briefly explain this Windows Firewall event (ID: {event_id}) in simple terms. [/INST]"
        
        interpretation = self.local_llm.generate(prompt, max_tokens=100)
        
        # Request state transition
        self.kernel.emit_event(self.name, "state.transition.alert", {
            "message": interpretation,
            "priority": 1,
            "metadata": event_data
        })
    
    def _process_user_query(self, event_data: Dict[str, Any]):
        """Process user message via LLM with intelligent model selection"""
        message = event_data.get("message", "")
        use_external = event_data.get("use_external", False)
        
        if not message:
            return
        
        logger.info(f"Processing user query: {message[:50]}...")
        
        # Try to inject system context if needed (for time, system info queries)
        try:
            # Access kernel's module registry through the parent kernel
            # This is a bit hacky but necessary since KernelAPI doesn't expose modules
            from kernel.kernel import Kernel
            for obj in self.kernel.__dict__.values():
                if isinstance(obj, Kernel):
                    if "system" in obj._modules:
                        system_module = obj._modules["system"]
                        if hasattr(system_module, 'inject_context_if_needed'):
                            message = system_module.inject_context_if_needed(message)
                    break
        except Exception as e:
            logger.debug(f"Could not inject system context: {e}")
        
        # Detect simple greetings and return instant canned responses
        message_lower = message.lower().strip()
        simple_greetings = {
            'hi': 'Hello!',
            'hello': 'Hello!',
            'hey': 'Hello!',
            'sup': 'Hello!',
            'yo': 'Hello!',
            'greetings': 'Hello!',
            'howdy': 'Hello!',
            'good morning': 'Hello!',
            'good afternoon': 'Hello!',
            'good evening': 'Hello!'
        }
        
        if message_lower in simple_greetings:
            # Instant response without LLM call
            response = simple_greetings[message_lower]
            logger.info(f"Instant greeting response: {response}")
        else:
            # Choose LLM provider
            llm = self.external_llm if (use_external and self.external_llm) else self.local_llm
            
            if not llm:
                response = "Local LLM not available."
                logger.warning("LLM not available - no model configured")
            else:
                try:
                    # Use LLM for everything else with aggressive speed settings
                    # Add instruction to ignore typos and be direct
                    prompt = f"[INST] Answer directly and concisely. Ignore any typos. {message} [/INST]"
                    response = llm.generate(
                        prompt, 
                        max_tokens=60,
                        temperature=0.3,
                        top_k=10,
                        top_p=0.5,
                        repeat_penalty=1.1,
                        mirostat_mode=2
                    )
                    logger.info(f"Generated response: {response[:50]}...")
                except Exception as e:
                    response = f"Error generating response: {str(e)}"
                    logger.error(f"LLM generation error: {e}")
        
        # Send response via IPC
        logger.info("Sending LLM response via IPC")
        self.kernel.emit_event(self.name, "ipc.send_message", {
            "type": "llm_response",
            "data": {"message": response}
        })
