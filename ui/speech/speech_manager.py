"""
E.V3 Speech Manager
Handles text-to-speech generation, audio playback, and animation sync
Supports neural TTS models and sample-based playback
"""

import io
import json
import wave
from pathlib import Path
from typing import Optional, Dict, Tuple
import numpy as np
from loguru import logger

# Audio playback (using pygame for cross-platform support)
try:
    import pygame.mixer as mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available - audio playback disabled")

from .voicepack_loader import VoicepackLoader, VoicepackInfo


class SpeechManager:
    """
    Manages speech synthesis and playback
    - Loads and switches between voicepacks
    - Generates speech using neural TTS or plays samples
    - Applies audio filters and emotion modulation
    - Provides phoneme data for lip-sync
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.speech_config = config.get('speech', {})
        
        # Initialize audio mixer
        if PYGAME_AVAILABLE:
            try:
                mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                self.audio_enabled = True
                logger.info("Audio mixer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize audio mixer: {e}")
                self.audio_enabled = False
        else:
            self.audio_enabled = False
        
        # Voicepack management
        self.loader = VoicepackLoader()
        self.active_voicepack: Optional[VoicepackInfo] = None
        self.tts_engine = None
        
        # Load voicepacks
        self._initialize_voicepacks()
        
        logger.info("Speech manager initialized")
    
    def _initialize_voicepacks(self):
        """Scan and load voicepacks"""
        voicepacks = self.loader.scan_voicepacks()
        
        if not voicepacks:
            logger.warning("No voicepacks found. Speech will be text-only.")
            return
        
        # Select active voicepack
        active_name = self.speech_config.get('active_voicepack')
        
        if active_name:
            voicepack = self.loader.get_voicepack(active_name)
            if voicepack:
                self.set_voicepack(active_name)
            else:
                logger.warning(f"Configured voicepack '{active_name}' not found")
                # Fall back to first available
                self.set_voicepack(voicepacks[0].path.name)
        else:
            # Use first available voicepack
            self.set_voicepack(voicepacks[0].path.name)
    
    def set_voicepack(self, name: str) -> bool:
        """
        Switch to a different voicepack (hot-swap)
        Returns True if successful
        """
        voicepack = self.loader.get_voicepack(name)
        if not voicepack:
            logger.error(f"Voicepack '{name}' not found")
            return False
        
        logger.info(f"Switching to voicepack: {voicepack.name}")
        
        # Unload previous TTS engine
        if self.tts_engine:
            self._unload_tts_engine()
        
        self.active_voicepack = voicepack
        
        # Initialize TTS engine if neural
        if voicepack.type in ['neural', 'hybrid']:
            if not self._load_tts_engine(voicepack):
                logger.error("Failed to load TTS engine")
                return False
        
        logger.info(f"Active voicepack: {voicepack.name}")
        return True
    
    def _load_tts_engine(self, voicepack: VoicepackInfo) -> bool:
        """Load neural TTS engine based on config"""
        neural_config = voicepack.config['neural']
        engine_type = neural_config['engine']
        
        try:
            if engine_type == 'piper':
                self.tts_engine = PiperTTSEngine(voicepack)
            elif engine_type == 'coqui':
                self.tts_engine = CoquiTTSEngine(voicepack)
            elif engine_type == 'espeak':
                self.tts_engine = ESpeakEngine(voicepack)
            else:
                logger.error(f"Unknown TTS engine: {engine_type}")
                return False
            
            logger.info(f"Loaded TTS engine: {engine_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load TTS engine: {e}")
            return False
    
    def _unload_tts_engine(self):
        """Unload current TTS engine"""
        if hasattr(self.tts_engine, 'cleanup'):
            self.tts_engine.cleanup()
        self.tts_engine = None
    
    def speak(
        self, 
        text: str, 
        emotion: str = "neutral",
        blocking: bool = False
    ) -> Optional[Dict]:
        """
        Generate and play speech
        
        Args:
            text: Text to speak
            emotion: Emotion tag (affects voice parameters)
            blocking: Wait for speech to finish
        
        Returns:
            Dict with audio info and phoneme data for animation sync
            None if failed
        """
        if not self.active_voicepack:
            logger.warning("No active voicepack - speech disabled")
            return None
        
        logger.debug(f"Speaking: '{text}' [emotion: {emotion}]")
        
        # Get voice parameters for this emotion
        params = self._get_emotion_parameters(emotion)
        
        # Try sample-based first if available
        if self.active_voicepack.type in ['samples', 'hybrid']:
            audio_data = self._try_sample_playback(text, emotion, params)
            if audio_data:
                return self._play_audio(audio_data, blocking)
        
        # Fall back to neural TTS
        if self.active_voicepack.type in ['neural', 'hybrid']:
            if self.tts_engine:
                audio_data = self._generate_neural_speech(text, params)
                if audio_data:
                    return self._play_audio(audio_data, blocking)
        
        # Fallback behavior
        return self._handle_fallback(text)
    
    def _get_emotion_parameters(self, emotion: str) -> Dict:
        """Get voice parameters adjusted for emotion"""
        # Start with base parameters
        base_params = self.active_voicepack.config.get('parameters', {})
        params = {
            'pitch': base_params.get('pitch', 1.0),
            'speed': base_params.get('speed', 1.0),
            'volume': base_params.get('volume', 1.0),
            'energy': base_params.get('energy', 1.0)
        }
        
        # Apply emotion modulation
        emotion_map = self.active_voicepack.config.get('emotion_map', {})
        if emotion in emotion_map:
            emotion_params = emotion_map[emotion]
            for key in ['pitch', 'speed', 'volume', 'energy']:
                if key in emotion_params:
                    params[key] *= emotion_params[key]
        
        return params
    
    def _try_sample_playback(
        self, 
        text: str, 
        emotion: str, 
        params: Dict
    ) -> Optional[Tuple[np.ndarray, int]]:
        """Try to find and load a pre-recorded sample"""
        samples_config = self.active_voicepack.config['samples']
        samples_folder = self.active_voicepack.path / samples_config.get('folder', 'samples')
        
        # Check if there's a direct mapping
        mapping = samples_config.get('mapping', {})
        text_lower = text.lower().strip()
        
        sample_file = None
        
        # Try exact match
        if text_lower in mapping:
            sample_file = samples_folder / mapping[text_lower]
        
        # Try with emotion suffix
        emotion_map = self.active_voicepack.config.get('emotion_map', {})
        if emotion in emotion_map:
            emotion_suffix = emotion_map[emotion].get('sample_suffix', '')
            if emotion_suffix:
                emotion_key = f"{text_lower}{emotion_suffix}"
                if emotion_key in mapping:
                    sample_file = samples_folder / mapping[emotion_key]
        
        if sample_file and sample_file.exists():
            try:
                return self._load_audio_file(sample_file, params)
            except Exception as e:
                logger.error(f"Failed to load sample {sample_file}: {e}")
        
        return None
    
    def _load_audio_file(
        self, 
        filepath: Path, 
        params: Dict
    ) -> Tuple[np.ndarray, int]:
        """Load audio file and apply parameter adjustments"""
        # TODO: Implement audio loading and processing
        # For now, return None (will be implemented with audio library)
        logger.debug(f"Loading audio file: {filepath}")
        return None
    
    def _generate_neural_speech(
        self, 
        text: str, 
        params: Dict
    ) -> Optional[Tuple[np.ndarray, int, list]]:
        """
        Generate speech using neural TTS engine
        Returns (audio_array, sample_rate, phoneme_data)
        """
        if not self.tts_engine:
            return None
        
        try:
            return self.tts_engine.synthesize(text, params)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None
    
    def _play_audio(
        self, 
        audio_data: Tuple, 
        blocking: bool
    ) -> Dict:
        """
        Play generated audio
        Returns info dict for animation sync
        """
        if not self.audio_enabled:
            logger.debug("Audio playback disabled")
            return {'duration': 0, 'phonemes': []}
        
        if not audio_data:
            return None
        
        # Unpack audio data
        if len(audio_data) == 2:
            audio_array, sample_rate = audio_data
            phonemes = []
        else:
            audio_array, sample_rate, phonemes = audio_data
        
        # Apply filters
        audio_array = self._apply_filters(audio_array, sample_rate)
        
        # Calculate duration
        duration = len(audio_array) / sample_rate
        
        # Play audio (TODO: implement actual playback)
        logger.debug(f"Playing audio: {duration:.2f}s, {len(phonemes)} phonemes")
        
        return {
            'duration': duration,
            'phonemes': phonemes,
            'sample_rate': sample_rate
        }
    
    def _apply_filters(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply audio post-processing filters"""
        filters_config = self.active_voicepack.config.get('filters', {})
        
        # Apply filters if enabled
        # TODO: Implement reverb, EQ, compressor
        # For now, return unprocessed audio
        
        return audio
    
    def _handle_fallback(self, text: str) -> Optional[Dict]:
        """Handle speech generation failure"""
        fallback_config = self.active_voicepack.config.get('fallback', {})
        behavior = fallback_config.get('behavior', 'text_only')
        
        logger.warning(f"Speech generation failed, fallback: {behavior}")
        
        if behavior == 'silent':
            return None
        elif behavior == 'text_only':
            # Just display text, no audio
            return {'duration': 0, 'phonemes': [], 'text_only': True}
        elif behavior == 'beep':
            # TODO: Play a simple beep sound
            return {'duration': 0.5, 'phonemes': []}
        
        return None
    
    def reload_voicepacks(self):
        """Rescan for voicepacks (hot-swap support)"""
        logger.info("Rescanning voicepacks...")
        current_name = self.active_voicepack.path.name if self.active_voicepack else None
        
        self.loader.scan_voicepacks()
        
        # Try to restore active voicepack
        if current_name:
            self.set_voicepack(current_name)
    
    def get_available_voicepacks(self) -> list:
        """Get list of available voicepack names"""
        return self.loader.list_voicepacks()
    
    def stop(self):
        """Stop current playback"""
        if self.audio_enabled and mixer:
            mixer.stop()


# TTS Engine Implementations

class PiperTTSEngine:
    """Piper TTS engine wrapper"""
    
    def __init__(self, voicepack: VoicepackInfo):
        self.voicepack = voicepack
        neural_config = voicepack.config['neural']
        
        model_path = voicepack.path / neural_config['model_path']
        
        # Try to import piper
        try:
            # Piper requires piper_phonemize library
            # Installation: pip install piper-tts
            logger.info(f"Loading Piper model: {model_path}")
            # TODO: Implement actual Piper loading
            # from piper import PiperVoice
            # self.voice = PiperVoice.load(str(model_path))
            logger.warning("Piper TTS not yet implemented - placeholder")
            
        except ImportError:
            logger.error("Piper TTS not installed. Install with: pip install piper-tts")
            raise
    
    def synthesize(
        self, 
        text: str, 
        params: Dict
    ) -> Tuple[np.ndarray, int, list]:
        """
        Synthesize speech with Piper
        Returns (audio, sample_rate, phonemes)
        """
        # TODO: Implement actual synthesis
        # audio = self.voice.synthesize(text, **params)
        # return audio, 22050, []
        
        logger.debug(f"Piper synthesize: {text}")
        # Return dummy data for now
        return None


class CoquiTTSEngine:
    """Coqui TTS engine wrapper"""
    
    def __init__(self, voicepack: VoicepackInfo):
        self.voicepack = voicepack
        logger.warning("Coqui TTS not yet implemented - placeholder")
    
    def synthesize(self, text: str, params: Dict) -> Tuple[np.ndarray, int, list]:
        logger.debug(f"Coqui synthesize: {text}")
        return None


class ESpeakEngine:
    """eSpeak TTS engine wrapper (basic fallback)"""
    
    def __init__(self, voicepack: VoicepackInfo):
        self.voicepack = voicepack
        logger.warning("eSpeak TTS not yet implemented - placeholder")
    
    def synthesize(self, text: str, params: Dict) -> Tuple[np.ndarray, int, list]:
        logger.debug(f"eSpeak synthesize: {text}")
        return None
