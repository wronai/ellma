"""
Audio Commands Module for ELLMa

Provides commands for text-to-speech and speech-to-text functionality.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile

from rich.console import Console
from rich.panel import Panel

from ellma.commands.base import BaseCommand, SimpleCommand, CommandError
from ellma.modules.tts import TTSModule, TTSBackend
from ellma.modules.stt import STTModule, STTBackend


class AudioCommands(BaseCommand):
    """Audio processing commands for ELLMa."""
    
    def __init__(self, agent):
        """Initialize audio commands."""
        super().__init__(agent)
        self.name = "audio"
        self.description = "Audio processing commands (TTS/STT)"
        self.console = Console()
        
        # Initialize TTS and STT modules with error handling
        self.tts = None
        self.stt = None
        self._initialize_modules()
    
    def _initialize_modules(self):
        """Initialize TTS and STT modules with error handling"""
        # Initialize TTS
        try:
            self.tts = TTSModule()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not initialize TTS module: {e}[/yellow]")
            self.console.print("[yellow]TTS functionality will be disabled.[/yellow]")
        
        # Initialize STT
        try:
            self.stt = STTModule()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not initialize STT module: {e}[/yellow]")
            self.console.print("[yellow]STT functionality will be disabled.[/yellow]")
    
    def speak(self, text: str, backend: str = None, **kwargs) -> Dict[str, Any]:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            backend: TTS backend to use (gtts, pyttsx)
            **kwargs: Additional TTS parameters
            
        Returns:
            Dict with status and message
        """
        if not self.tts:
            return {
                "status": "error", 
                "message": "TTS is not available. Please check if required dependencies are installed."
            }
            
        try:
            if backend:
                kwargs['backend'] = TTSBackend(backend.lower())
            
            success = self.tts.speak(text, **kwargs)
            if success:
                return {"status": "success", "message": "Speech played successfully"}
            else:
                return {"status": "error", "message": "Failed to play speech"}
        except DependencyError as e:
            return {"status": "error", "message": f"Dependency error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"TTS error: {str(e)}"}
    
    def save_speech(self, text: str, filename: str, backend: str = "gtts", **kwargs) -> Dict[str, Any]:
        """
        Convert text to speech and save to a file
        
        Args:
            text: Text to convert
            filename: Output filename
            backend: TTS backend to use (gtts, pyttsx)
            **kwargs: Additional TTS parameters
            
        Returns:
            Dict with status and message
        """
        try:
            kwargs['backend'] = TTSBackend(backend.lower())
            success = self.tts.save_to_file(text, filename, **kwargs)
            if success:
                return {"status": "success", "message": f"Speech saved to {filename}"}
            else:
                return {"status": "error", "message": "Failed to save speech"}
        except Exception as e:
            return {"status": "error", "message": f"TTS save error: {str(e)}"}
    
    def listen(self, timeout: float = 5.0, backend: str = None, **kwargs) -> Dict[str, Any]:
        """
        Listen to microphone and return recognized text
        
        Args:
            timeout: Seconds to wait for speech input
            backend: STT backend to use (whisper, google, sphinx)
            **kwargs: Additional STT parameters
            
        Returns:
            Dict with status, text, and additional info
        """
        if not self.stt:
            return {
                "status": "error", 
                "message": "STT is not available. Please check if required dependencies are installed."
            }
            
        try:
            # Listen and recognize
            text = self.stt.listen(timeout=timeout, **kwargs)
            
            if text:
                backend_used = getattr(self.stt.config, 'backend', None)
                return {
                    "status": "success",
                    "text": text,
                    "backend": backend_used.value if backend_used else "unknown"
                }
            else:
                return {"status": "no_speech", "message": "No speech detected"}
                
        except DependencyError as e:
            return {"status": "error", "message": f"Dependency error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"STT error: {str(e)}"}
    
    def transcribe(self, filename: str, backend: str = "whisper") -> Dict[str, Any]:
        """
        Transcribe speech from an audio file
        
        Args:
            filename: Path to audio file
            backend: STT backend to use (whisper, google, sphinx)
            
        Returns:
            Dict with status, text, and additional info
        """
        try:
            # Update STT backend if specified
            if backend:
                self.stt.config.backend = STTBackend(backend.lower())
            
            # Transcribe the file
            text = self.stt.recognize_from_file(filename)
            
            if text:
                return {
                    "status": "success",
                    "text": text,
                    "backend": self.stt.config.backend.value
                }
            else:
                return {"status": "error", "message": "Failed to transcribe audio"}
                
        except Exception as e:
            return {"status": "error", "message": f"Transcription error: {str(e)}"}
    
    def list_backends(self) -> Dict[str, List[str]]:
        """
        List available backends for TTS and STT
        
        Returns:
            Dict with available backends for TTS and STT
        """
        return {
            "tts_backends": [b.value for b in TTSBackend],
            "stt_backends": [b.value for b in STTBackend]
        }
