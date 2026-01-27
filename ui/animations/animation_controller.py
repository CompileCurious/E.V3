"""
Animation Controller for 3D Character
Handles idle breathing, eye blinking, state-based animations
"""

import numpy as np
import time
import random
from typing import Optional, Dict, Any
from loguru import logger

from .model_loader import Model3D


class AnimationController:
    """
    Controls character animations
    """
    
    def __init__(self, model: Model3D, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.time = 0.0
        
        # Animation states
        self.is_breathing = config.get("ui", {}).get("animations", {}).get("idle_breathing", {}).get("enabled", True)
        self.is_blinking = config.get("ui", {}).get("animations", {}).get("eye_blinking", {}).get("enabled", True)
        
        # Breathing parameters
        self.breathing_speed = config.get("ui", {}).get("animations", {}).get("idle_breathing", {}).get("speed", 0.5)
        self.breathing_intensity = config.get("ui", {}).get("animations", {}).get("idle_breathing", {}).get("intensity", 0.3)
        
        # Blinking parameters
        self.blink_interval_min = config.get("ui", {}).get("animations", {}).get("eye_blinking", {}).get("interval_min", 2.0)
        self.blink_interval_max = config.get("ui", {}).get("animations", {}).get("eye_blinking", {}).get("interval_max", 6.0)
        self.blink_duration = config.get("ui", {}).get("animations", {}).get("eye_blinking", {}).get("duration", 0.15)
        
        self.next_blink_time = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        self.blink_start_time = 0.0
        self.is_currently_blinking = False
        
        # Current state
        self.current_state = "idle"
        self.state_transition_time = 0.0
        
        logger.info("Animation controller initialized")
    
    def update(self, dt: float):
        """Update animations"""
        self.time += dt
        
        # Update breathing
        if self.is_breathing:
            self._update_breathing()
        
        # Update blinking
        if self.is_blinking:
            self._update_blinking()
        
        # Update state-based animations
        self._update_state_animation()
    
    def _update_breathing(self):
        """Update idle breathing animation"""
        # Breathing cycle using sine wave
        breath_phase = np.sin(self.time * self.breathing_speed * 2.0 * np.pi)
        breath_amount = breath_phase * self.breathing_intensity
        
        # Apply breathing to chest/torso bones if they exist
        # This is simplified - proper implementation would target specific bones
        if self.model.bones:
            # Example: Scale chest bone
            for bone in self.model.bones:
                if "chest" in bone.name.lower() or "spine" in bone.name.lower():
                    # Expand/contract chest
                    bone.scale[1] = 1.0 + breath_amount * 0.05
                    bone.scale[2] = 1.0 + breath_amount * 0.05
    
    def _update_blinking(self):
        """Update eye blinking animation"""
        current_time = time.time()
        
        # Check if it's time to blink
        if not self.is_currently_blinking and current_time >= self.next_blink_time:
            self.is_currently_blinking = True
            self.blink_start_time = current_time
        
        # Blink animation
        if self.is_currently_blinking:
            blink_progress = (current_time - self.blink_start_time) / self.blink_duration
            
            if blink_progress >= 1.0:
                # Blink finished
                self.is_currently_blinking = False
                self.next_blink_time = current_time + random.uniform(
                    self.blink_interval_min,
                    self.blink_interval_max
                )
                blink_amount = 0.0
            else:
                # Blink in progress (close then open)
                if blink_progress < 0.5:
                    # Closing
                    blink_amount = blink_progress * 2.0
                else:
                    # Opening
                    blink_amount = (1.0 - blink_progress) * 2.0
            
            # Apply blink to eye blendshapes
            if "eye_blink_left" in self.model.blendshapes:
                self.model.set_blendshape_weight("eye_blink_left", blink_amount)
            if "eye_blink_right" in self.model.blendshapes:
                self.model.set_blendshape_weight("eye_blink_right", blink_amount)
    
    def _update_state_animation(self):
        """Update animation based on current state"""
        if self.current_state == "idle":
            # Idle pose - already handled by breathing
            pass
        
        elif self.current_state == "alert":
            # Alert pose - lean forward slightly, eyes wide
            self._apply_alert_pose()
        
        elif self.current_state == "reminder":
            # Reminder pose - gentle head tilt
            self._apply_reminder_pose()
        
        elif self.current_state == "scanning":
            # Scanning pose - look around
            self._apply_scanning_pose()
    
    def _apply_alert_pose(self):
        """Apply alert pose animation"""
        # Lean forward
        if self.model.bones:
            for bone in self.model.bones:
                if "spine" in bone.name.lower():
                    bone.rotation[0] = 10.0  # Lean forward 10 degrees
        
        # Eyes wide (reduce blink blendshape)
        if "eye_blink_left" in self.model.blendshapes:
            self.model.set_blendshape_weight("eye_blink_left", 0.0)
        if "eye_blink_right" in self.model.blendshapes:
            self.model.set_blendshape_weight("eye_blink_right", 0.0)
    
    def _apply_reminder_pose(self):
        """Apply reminder pose animation"""
        # Gentle head tilt
        if self.model.bones:
            for bone in self.model.bones:
                if "head" in bone.name.lower():
                    bone.rotation[2] = 5.0 * np.sin(self.time * 2.0)  # Gentle sway
    
    def _apply_scanning_pose(self):
        """Apply scanning pose animation"""
        # Look around (head rotation)
        if self.model.bones:
            for bone in self.model.bones:
                if "head" in bone.name.lower():
                    # Look left and right
                    bone.rotation[1] = 15.0 * np.sin(self.time * 0.5)
    
    def set_state(self, state: str):
        """Change animation state"""
        if state != self.current_state:
            logger.info(f"Animation state: {self.current_state} -> {state}")
            self.current_state = state
            self.state_transition_time = self.time
    
    def play_gesture(self, gesture_name: str):
        """Play a specific gesture animation"""
        logger.info(f"Playing gesture: {gesture_name}")
        # Implementation would trigger specific animation sequences
        pass
    
    def enable_breathing(self, enabled: bool):
        """Enable/disable breathing animation"""
        self.is_breathing = enabled
    
    def enable_blinking(self, enabled: bool):
        """Enable/disable blinking animation"""
        self.is_blinking = enabled
    
    def set_expression(self, expression: str, intensity: float = 1.0):
        """
        Set facial expression using blendshapes
        
        Common expressions: happy, sad, angry, surprised, neutral
        """
        # Map expressions to blendshape combinations
        expression_map = {
            "happy": {"mouth_smile": 0.8, "eye_happy": 0.6},
            "sad": {"mouth_frown": 0.7, "eye_sad": 0.5},
            "surprised": {"mouth_o": 0.9, "eye_wide": 0.8},
            "angry": {"mouth_frown": 0.6, "brow_angry": 0.7},
            "neutral": {}
        }
        
        # Reset all expression blendshapes
        for name in self.model.blendshapes:
            if any(x in name.lower() for x in ["mouth", "eye", "brow"]):
                self.model.set_blendshape_weight(name, 0.0)
        
        # Apply new expression
        if expression in expression_map:
            for blendshape, weight in expression_map[expression].items():
                if blendshape in self.model.blendshapes:
                    self.model.set_blendshape_weight(blendshape, weight * intensity)
