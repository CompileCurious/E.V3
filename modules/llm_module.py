"""
LLM Module
Provides local and external LLM capabilities
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
        """Process user message via LLM"""
        message = event_data.get("message", "")
        use_external = event_data.get("use_external", False)
        
        if not message:
            return
        
        logger.info(f"Processing user query: {message[:50]}...")
        
        # Choose LLM provider
        llm = self.external_llm if (use_external and self.external_llm) else self.local_llm
        
        if not llm:
            response = (
                "⚠️ LLM not configured.\n\n"
                "To use the AI assistant, you need to:\n"
                "1. Install llama-cpp-python: pip install llama-cpp-python\n"
                "2. Download Mistral 7B model from HuggingFace\n"
                "3. Place it in models/llm/ folder\n\n"
                "See models/MODEL_SETUP.md for detailed instructions."
            )
            logger.warning("LLM not available - no model configured")
        else:
            try:
                prompt = f"[INST] {message} [/INST]"
                response = llm.generate(prompt, max_tokens=256)
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
