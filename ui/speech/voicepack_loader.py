"""
E.V3 Voicepack Loader
Scans, loads, and manages voicepacks with hot-swap support
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class VoicepackInfo:
    """Voicepack metadata"""
    name: str
    version: str
    author: Optional[str]
    description: Optional[str]
    type: str  # neural, samples, hybrid
    path: Path
    config: Dict
    
    def __repr__(self):
        return f"Voicepack({self.name} v{self.version} [{self.type}])"


class VoicepackLoader:
    """
    Loads and manages voicepacks from the models/speech/ directory
    - Scans for voicepack folders
    - Validates config.json
    - Supports hot-swapping
    """
    
    def __init__(self, voicepack_dir: str = "models/speech"):
        self.voicepack_dir = Path(voicepack_dir)
        self.voicepacks: Dict[str, VoicepackInfo] = {}
        self._last_scan_time = 0
        
        logger.info(f"Voicepack loader initialized: {self.voicepack_dir}")
    
    def scan_voicepacks(self) -> List[VoicepackInfo]:
        """
        Scan for available voicepacks
        Returns list of valid voicepacks
        """
        self.voicepacks.clear()
        
        if not self.voicepack_dir.exists():
            logger.warning(f"Voicepack directory does not exist: {self.voicepack_dir}")
            self.voicepack_dir.mkdir(parents=True, exist_ok=True)
            return []
        
        found_count = 0
        
        # Scan each subdirectory
        for folder in self.voicepack_dir.iterdir():
            if not folder.is_dir():
                continue
            
            config_file = folder / "config.json"
            if not config_file.exists():
                logger.debug(f"Skipping {folder.name}: no config.json")
                continue
            
            try:
                # Load and validate config
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                voicepack = self._validate_and_create_voicepack(folder, config)
                if voicepack:
                    self.voicepacks[folder.name] = voicepack
                    found_count += 1
                    logger.info(f"Loaded voicepack: {voicepack}")
                
            except Exception as e:
                logger.error(f"Failed to load voicepack {folder.name}: {e}")
        
        logger.info(f"Scan complete: {found_count} voicepacks loaded")
        return list(self.voicepacks.values())
    
    def _validate_and_create_voicepack(
        self, 
        folder: Path, 
        config: Dict
    ) -> Optional[VoicepackInfo]:
        """
        Validate config and create VoicepackInfo
        """
        # Check required fields
        required_fields = ['name', 'version', 'type']
        for field in required_fields:
            if field not in config:
                logger.error(f"Voicepack {folder.name} missing required field: {field}")
                return None
        
        # Validate type
        vtype = config['type']
        if vtype not in ['neural', 'samples', 'hybrid']:
            logger.error(f"Invalid voicepack type: {vtype}")
            return None
        
        # Validate type-specific requirements
        if vtype in ['neural', 'hybrid']:
            if 'neural' not in config:
                logger.error(f"Neural voicepack {folder.name} missing 'neural' config")
                return None
            
            # Check model file exists
            neural_config = config['neural']
            if 'model_path' not in neural_config:
                logger.error(f"Neural config missing 'model_path'")
                return None
            
            model_path = folder / neural_config['model_path']
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return None
        
        if vtype in ['samples', 'hybrid']:
            if 'samples' not in config:
                logger.error(f"Sample voicepack {folder.name} missing 'samples' config")
                return None
            
            # Check samples folder exists
            samples_config = config['samples']
            samples_folder = folder / samples_config.get('folder', 'samples')
            if not samples_folder.exists():
                logger.warning(f"Samples folder not found: {samples_folder}")
        
        # Create VoicepackInfo
        return VoicepackInfo(
            name=config['name'],
            version=config['version'],
            author=config.get('author'),
            description=config.get('description'),
            type=vtype,
            path=folder,
            config=config
        )
    
    def get_voicepack(self, name: str) -> Optional[VoicepackInfo]:
        """
        Get voicepack by folder name
        """
        return self.voicepacks.get(name)
    
    def list_voicepacks(self) -> List[str]:
        """
        Get list of available voicepack names
        """
        return list(self.voicepacks.keys())
    
    def reload_voicepack(self, name: str) -> bool:
        """
        Reload a specific voicepack (hot-swap support)
        Returns True if successful
        """
        folder = self.voicepack_dir / name
        config_file = folder / "config.json"
        
        if not config_file.exists():
            logger.error(f"Cannot reload {name}: config.json not found")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            voicepack = self._validate_and_create_voicepack(folder, config)
            if voicepack:
                self.voicepacks[name] = voicepack
                logger.info(f"Reloaded voicepack: {voicepack}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to reload voicepack {name}: {e}")
            return False
    
    def check_for_changes(self) -> List[str]:
        """
        Check if any voicepacks have changed on disk
        Returns list of changed voicepack names
        """
        changed = []
        
        for name, voicepack in self.voicepacks.items():
            config_file = voicepack.path / "config.json"
            try:
                current_mtime = config_file.stat().st_mtime
                if current_mtime > self._last_scan_time:
                    changed.append(name)
            except:
                pass
        
        self._last_scan_time = Path(self.voicepack_dir).stat().st_mtime
        return changed
