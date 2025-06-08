"""
Text-to-Speech (TTS) Module for ELLMa

Provides text-to-speech functionality using various backends.
"""

import os
import tempfile
import importlib
from typing import Optional, Union, BinaryIO, Type, Any, Dict
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from rich.console import Console

# Try to import optional dependencies
try:
    import pyttsx3
    PYTTSX_AVAILABLE = True
except ImportError:
    PYTTSX_AVAILABLE = False

try:
    from gtts import gTTS
    from pydub import AudioSegment
    from pydub.playback import play
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Custom exception for missing dependencies
class DependencyError(ImportError):
    """Exception raised when a required dependency is missing."""
    def __init__(self, package_name: str, feature: str):
        self.package_name = package_name
        self.feature = feature
        super().__init__(f"The '{package_name}' package is required for {feature} but is not installed. "
                        f"Please install it with: pip install {package_name}")

# Type alias for better type hints
AudioBackend = Any  # Could be more specific based on actual usage

class TTSBackend(Enum):
    """Available TTS backends"""
    GTTS = "gtts"  # Google Text-to-Speech (online)
    PYTTSX = "pyttsx3"  # Offline TTS using system voices

@dataclass
class TTSConfig:
    """Configuration for TTS"""
    backend: TTSBackend = TTSBackend.PYTTSX
    language: str = "en"
    slow: bool = False
    volume: float = 1.0
    rate: int = 150  # Words per minute

class TTSModule:
    """Text-to-Speech module for ELLMa"""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize TTS module with configuration"""
        self.config = TTSConfig(**(config or {}))
        self.console = Console()
        self.engine = None
        self.available_backends = self._check_available_backends()
        self._init_engine()
    
    def _check_available_backends(self) -> Dict[str, bool]:
        """Check which TTS backends are available"""
        return {
            'pyttsx3': PYTTSX_AVAILABLE,
            'gtts': GTTS_AVAILABLE
        }
    
    def _require_backend(self, backend_name: str):
        """Check if a backend is available, raise helpful error if not"""
        if not self.available_backends.get(backend_name, False):
            if backend_name == 'pyttsx3' and not PYTTS_AVAILABLE:
                raise DependencyError('pyttsx3', 'offline TTS functionality')
            elif backend_name == 'gtts' and not GTTS_AVAILABLE:
                raise DependencyError('gTTS', 'Google TTS functionality')
            else:
                raise ValueError(f"Unsupported backend: {backend_name}")
    
    def _init_engine(self):
        """Initialize the TTS engine based on configuration"""
        if self.config.backend == TTSBackend.PYTTSX:
            try:
                self._require_backend('pyttsx3')
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', self.config.rate)
                self.engine.setProperty('volume', self.config.volume)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to initialize pyttsx3: {e}[/yellow]")
                if GTTS_AVAILABLE:
                    self.console.print("Falling back to gTTS")
                    self.config.backend = TTSBackend.GTTS
                else:
                    self.console.print("[red]No TTS backends available. Please install pyttsx3 or gTTS.[/red]")
        elif self.config.backend == TTSBackend.GTTS and not GTTS_AVAILABLE:
            if PYTTSX_AVAILABLE:
                self.console.print("[yellow]gTTS not available. Falling back to pyttsx3.[/yellow]")
                self.config.backend = TTSBackend.PYTTSX
                self._init_engine()
            else:
                self.console.print("[red]No TTS backends available. Please install pyttsx3 or gTTS.[/red]")
    
    def speak(self, text: str, **kwargs) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            **kwargs: Override config (backend, language, slow, volume, rate)
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = {**self.config.__dict__, **kwargs}
        backend = TTSBackend(config.get('backend', self.config.backend))
        
        try:
            if backend == TTSBackend.GTTS:
                return self._speak_gtts(text, **config)
            else:  # PYTTSX
                return self._speak_pyttsx(text, **config)
        except Exception as e:
            self.console.print(f"[red]Error in TTS: {e}[/red]")
            return False
    
    def _speak_gtts(self, text: str, language: str = "en", slow: bool = False, **_) -> bool:
        """Use Google's gTTS for text-to-speech"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                tts = gTTS(text=text, lang=language, slow=slow)
                tts.save(fp.name)
                
                # Play the audio file
                audio = AudioSegment.from_mp3(fp.name)
                play(audio)
                
                # Clean up
                os.unlink(fp.name)
                return True
        except Exception as e:
            self.console.print(f"[red]gTTS Error: {e}[/red]")
            return False
    
    def _speak_pyttsx(self, text: str, rate: int = 150, volume: float = 1.0, **_) -> bool:
        """Use pyttsx3 for offline text-to-speech"""
        if not self.engine:
            self.console.print("[red]TTS engine not initialized[/red]")
            return False
            
        try:
            # Save current settings
            original_rate = self.engine.getProperty('rate')
            original_volume = self.engine.getProperty('volume')
            
            # Apply new settings
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()
            
            # Restore original settings
            self.engine.setProperty('rate', original_rate)
            self.engine.setProperty('volume', original_volume)
            
            return True
        except Exception as e:
            self.console.print(f"[red]pyttsx3 Error: {e}[/red]")
            return False
    
    def save_to_file(self, text: str, filename: str, **kwargs) -> bool:
        """
        Convert text to speech and save to a file
        
        Args:
            text: Text to convert
            filename: Output filename
            **kwargs: Override config (backend, language, slow)
            
        Returns:
            bool: True if successful, False otherwise
        """
        config = {**self.config.__dict__, **kwargs}
        backend = TTSBackend(config.get('backend', self.config.backend))
        
        try:
            if backend == TTSBackend.GTTS:
                tts = gTTS(
                    text=text,
                    lang=config.get('language', 'en'),
                    slow=config.get('slow', False)
                )
                tts.save(filename)
                return True
            else:
                self.console.print("[yellow]Saving to file is only supported with gTTS backend[/yellow]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error saving TTS to file: {e}[/red]")
            return False

# Command-line interface for testing
if __name__ == "__main__":
    tts = TTSModule()
    print("Testing TTS module. Type 'exit' to quit.")
    
    while True:
        text = input("Enter text to speak: ")
        if text.lower() == 'exit':
            break
        tts.speak(text)
